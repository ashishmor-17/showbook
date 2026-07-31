// apps/inventory-service/internal/service/inventory_service.go
package service

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/inventory-service/internal/redislock"
	dbRepo "github.com/ashishmor-17/showbook/apps/inventory-service/internal/repository"
)

type InventoryService struct {
	repo  *dbRepo.SeatRepository
	redis *redislock.LockClient
	log   *zap.Logger
}

func NewInventoryService(repo *dbRepo.SeatRepository, redis *redislock.LockClient, log *zap.Logger) *InventoryService {
	return &InventoryService{repo: repo, redis: redis, log: log}
}

type Summary struct {
	Available int `json:"available"`
	Locked    int `json:"locked"`
	Booked    int `json:"booked"`
}

func (s *InventoryService) LockSeats(ctx context.Context, showtimeID string, seatCodes []string, bookingID string) error {
	// Try atomic lock acquisition in Redis
	success, conflictingKey, err := s.redis.AcquireLocks(ctx, showtimeID, seatCodes, bookingID, 10*time.Minute)
	if err != nil {
		return fmt.Errorf("redis lock failed: %w", err)
	}
	if !success {
		return fmt.Errorf("seats unavailable in lock manager (conflict on %s)", conflictingKey)
	}

	// Perform Postgres update via repository transaction wrapper
	lockedUntil := time.Now().Add(10 * time.Minute)
	err = s.repo.LockSeatsTx(ctx, showtimeID, seatCodes, bookingID, lockedUntil)
	if err != nil {
		_ = s.redis.ReleaseLocks(ctx, showtimeID, seatCodes, bookingID)
		return fmt.Errorf("database transaction lock failed: %w", err)
	}

	// Invalidate summary cache
	_ = s.redis.InvalidateSummary(ctx, showtimeID)

	return nil
}

func (s *InventoryService) ReleaseSeats(ctx context.Context, showtimeID string, seatCodes []string, bookingID string) error {
	// Release in Redis
	_ = s.redis.ReleaseLocks(ctx, showtimeID, seatCodes, bookingID)

	// Update Postgres status
	err := s.repo.ReleaseSeats(ctx, showtimeID, seatCodes, bookingID)
	if err != nil {
		return fmt.Errorf("db release seats failed: %w", err)
	}

	// Invalidate cache
	_ = s.redis.InvalidateSummary(ctx, showtimeID)

	return nil
}

func (s *InventoryService) ConfirmSeats(ctx context.Context, showtimeID string, seatCodes []string, bookingID string) error {
	// Update Postgres status to BOOKED in transaction block
	err := s.repo.ConfirmSeatsTx(ctx, showtimeID, seatCodes, bookingID)
	if err != nil {
		return fmt.Errorf("database transaction confirmation failed: %w", err)
	}

	// Delete Redis lock keys
	_ = s.redis.ReleaseLocks(ctx, showtimeID, seatCodes, bookingID)

	// Invalidate cache
	_ = s.redis.InvalidateSummary(ctx, showtimeID)

	return nil
}

func (s *InventoryService) GetSummary(ctx context.Context, showtimeID string) (Summary, error) {
	var summary Summary

	// Read Redis cache
	cachedVal, err := s.redis.GetSummary(ctx, showtimeID)
	if err == nil {
		if json.Unmarshal([]byte(cachedVal), &summary) == nil {
			return summary, nil
		}
	}

	// Read Postgres status counts
	counts, err := s.repo.GetStatusCounts(ctx, showtimeID)
	if err != nil {
		return summary, fmt.Errorf("db get status counts failed: %w", err)
	}

	summary.Available = counts["AVAILABLE"]
	summary.Locked = counts["LOCKED"]
	summary.Booked = counts["BOOKED"]

	// Save back to cache (TTL: 30s)
	data, _ := json.Marshal(summary)
	_ = s.redis.SetSummary(ctx, showtimeID, string(data), 30*time.Second)

	return summary, nil
}
