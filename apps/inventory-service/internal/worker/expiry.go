// apps/inventory-service/internal/worker/expiry.go
package worker

import (
	"context"
	"time"

	"github.com/google/uuid"
	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/inventory-service/internal/redislock"
	dbRepo "github.com/ashishmor-17/showbook/apps/inventory-service/internal/repository"
)

const LockExpiryAdvisoryID = 987654

// StartLockExpiryWorker runs a background ticker checking for expired seat locks using Postgres advisory locks
func StartLockExpiryWorker(ctx context.Context, repo *dbRepo.SeatRepository, rdb *redislock.LockClient, log *zap.Logger) {
	ticker := time.NewTicker(30 * time.Second)
	log.Info("Lock Expiry Background Worker initialized.")

	go func() {
		for {
			select {
			case <-ctx.Done():
				ticker.Stop()
				log.Info("Lock Expiry Background Worker stopped.")
				return
			case <-ticker.C:
				cleanupExpiredLocks(ctx, repo, rdb, log)
			}
		}
	}()
}

func cleanupExpiredLocks(ctx context.Context, repo *dbRepo.SeatRepository, rdb *redislock.LockClient, log *zap.Logger) {
	workCtx, cancel := context.WithTimeout(ctx, 20*time.Second)
	defer cancel()

	// Acquire distributed advisory lock
	acquired, err := repo.TryAdvisoryLock(workCtx, LockExpiryAdvisoryID)
	if err != nil {
		log.Error("Failed to acquire advisory lock", zap.Error(err))
		return
	}
	if !acquired {
		return
	}
	defer func() {
		_ = repo.AdvisoryUnlock(workCtx, LockExpiryAdvisoryID)
	}()

	// Fetch up to 500 expired locks in a batch
	expired, err := repo.GetExpiredLocks(workCtx, 500)
	if err != nil {
		log.Error("Failed to query expired seat locks", zap.Error(err))
		return
	}

	if len(expired) == 0 {
		return
	}

	log.Info("Found expired seat locks to release", zap.Int("count", len(expired)))

	expiredIDs := make([]uuid.UUID, len(expired))
	for i, item := range expired {
		expiredIDs[i] = item.ID
	}

	// Batch release in Postgres
	err = repo.ReleaseExpiredLocksBatch(workCtx, expiredIDs)
	if err != nil {
		log.Error("Failed to batch update expired seat statuses in Postgres", zap.Error(err))
		return
	}

	// Release locks in Redis and invalidate corresponding summaries
	for _, item := range expired {
		_ = rdb.ReleaseLocks(workCtx, item.ShowtimeID.String(), []string{item.SeatCode}, item.BookingID.String())
		_ = rdb.InvalidateSummary(workCtx, item.ShowtimeID.String())
	}

	log.Info("Batch cleanup of expired seat locks completed.", zap.Int("count", len(expired)))
}
