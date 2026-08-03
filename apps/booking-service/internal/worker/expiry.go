package worker

import (
	"context"
	"time"

	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/booking-service/internal/repository"
)

type ExpiryWorker struct {
	repo *repository.BookingRepository
	log  *zap.Logger
}

func NewExpiryWorker(
	repo *repository.BookingRepository,
	log *zap.Logger,
) *ExpiryWorker {
	return &ExpiryWorker{
		repo: repo,
		log:  log,
	}
}

func (w *ExpiryWorker) Start(ctx context.Context) {
	w.log.Info("Booking Expiry Worker started.")
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			w.log.Info("Stopping Expiry Worker...")
			return
		case <-ticker.C:
			w.expireUnpaidBookings(ctx)
		}
	}
}

func (w *ExpiryWorker) expireUnpaidBookings(ctx context.Context) {
	dbCtx, cancelDB := context.WithTimeout(ctx, 10*time.Second)
	expiredBookings, expiredSeats, err := w.repo.ExpireBookingsBulk(dbCtx, 500)
	cancelDB()

	if err != nil {
		w.log.Error("Failed executing bulk expiry query", zap.Error(err))
		return
	}

	for i, b := range expiredBookings {
		seatCodes := expiredSeats[i]
		w.log.Info("Unpaid booking expired", 
			zap.String("booking_ref", b.BookingRef), 
			zap.String("booking_id", b.ID.String()),
			zap.Strings("seat_codes", seatCodes),
		)
	}
}
