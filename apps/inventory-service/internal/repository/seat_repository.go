// apps/inventory-service/internal/repository/seat_repository.go
package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
)

type ExpiredLock struct {
	ID         uuid.UUID
	ShowtimeID uuid.UUID
	SeatCode   string
	BookingID  uuid.UUID
}

type SeatRepository struct {
	db *pgxpool.Pool
}

func NewSeatRepository(db *pgxpool.Pool) *SeatRepository {
	return &SeatRepository{db: db}
}

// LockSeatsTx updates seats in a transaction block, rolling back if row count doesn't match
func (r *SeatRepository) LockSeatsTx(ctx context.Context, showtimeID string, seatCodes []string, bookingID string, lockedUntil time.Time) error {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer func() { _ = tx.Rollback(ctx) }()

	query := `
		UPDATE seat_inventory 
		SET status = 'LOCKED', 
			locked_by_booking_id = $1, 
			locked_until = $2, 
			updated_at = NOW(), 
			version = version + 1
		WHERE showtime_id = $3 
		  AND seat_code = ANY($4) 
		  AND (status = 'AVAILABLE' OR (status = 'LOCKED' AND locked_by_booking_id = $1));
	`
	cmdTag, err := tx.Exec(ctx, query, bookingID, lockedUntil, showtimeID, seatCodes)
	if err != nil {
		return err
	}

	if cmdTag.RowsAffected() != int64(len(seatCodes)) {
		return fmt.Errorf("seats unavailable in database")
	}

	return tx.Commit(ctx)
}

// ReleaseSeats updates status back to AVAILABLE if matched
func (r *SeatRepository) ReleaseSeats(ctx context.Context, showtimeID string, seatCodes []string, bookingID string) error {
	query := `
		UPDATE seat_inventory 
		SET status = 'AVAILABLE', 
			locked_by_booking_id = NULL, 
			locked_until = NULL, 
			updated_at = NOW(), 
			version = version + 1
		WHERE showtime_id = $1 
		  AND seat_code = ANY($2) 
		  AND status = 'LOCKED' 
		  AND locked_by_booking_id = $3;
	`
	_, err := r.db.Exec(ctx, query, showtimeID, seatCodes, bookingID)
	return err
}

// ConfirmSeatsTx updates status to BOOKED in a transaction block, rolling back if row count mismatch
func (r *SeatRepository) ConfirmSeatsTx(ctx context.Context, showtimeID string, seatCodes []string, bookingID string) error {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer func() { _ = tx.Rollback(ctx) }()

	query := `
		UPDATE seat_inventory 
		SET status = 'BOOKED', 
			booked_by_booking_id = $1, 
			locked_by_booking_id = NULL, 
			locked_until = NULL, 
			updated_at = NOW(), 
			version = version + 1
		WHERE showtime_id = $2 
		  AND seat_code = ANY($3) 
		  AND status = 'LOCKED' 
		  AND locked_by_booking_id = $1;
	`
	cmdTag, err := tx.Exec(ctx, query, bookingID, showtimeID, seatCodes)
	if err != nil {
		return err
	}

	if cmdTag.RowsAffected() != int64(len(seatCodes)) {
		return fmt.Errorf("seats confirmation failed: row mismatch")
	}

	return tx.Commit(ctx)
}

// GetStatusCounts fetches seat counts grouped by status
func (r *SeatRepository) GetStatusCounts(ctx context.Context, showtimeID string) (map[string]int, error) {
	query := `
		SELECT status, COUNT(*) 
		FROM seat_inventory 
		WHERE showtime_id = $1 
		GROUP BY status;
	`
	rows, err := r.db.Query(ctx, query, showtimeID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	counts := make(map[string]int)
	for rows.Next() {
		var status string
		var count int
		if err := rows.Scan(&status, &count); err != nil {
			return nil, err
		}
		counts[status] = count
	}
	return counts, nil
}

func (r *SeatRepository) TryAdvisoryLock(ctx context.Context, lockID int64) (bool, error) {
	var acquired bool
	err := r.db.QueryRow(ctx, "SELECT pg_try_advisory_lock($1)", lockID).Scan(&acquired)
	return acquired, err
}

func (r *SeatRepository) AdvisoryUnlock(ctx context.Context, lockID int64) error {
	_, err := r.db.Exec(ctx, "SELECT pg_advisory_unlock($1)", lockID)
	return err
}

// GetExpiredLocks queries expired locks up to limit
func (r *SeatRepository) GetExpiredLocks(ctx context.Context, limit int) ([]ExpiredLock, error) {
	query := `
		SELECT id, showtime_id, seat_code, locked_by_booking_id 
		FROM seat_inventory 
		WHERE status = 'LOCKED' AND locked_until < NOW()
		LIMIT $1;
	`
	rows, err := r.db.Query(ctx, query, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var expired []ExpiredLock
	for rows.Next() {
		var item ExpiredLock
		if err := rows.Scan(&item.ID, &item.ShowtimeID, &item.SeatCode, &item.BookingID); err == nil {
			expired = append(expired, item)
		}
	}
	return expired, nil
}

// ReleaseExpiredLocksBatch updates a list of expired seat IDs back to AVAILABLE status in one query
func (r *SeatRepository) ReleaseExpiredLocksBatch(ctx context.Context, ids []uuid.UUID) error {
	if len(ids) == 0 {
		return nil
	}
	query := `
		UPDATE seat_inventory 
		SET status = 'AVAILABLE', 
			locked_by_booking_id = NULL, 
			locked_until = NULL, 
			updated_at = NOW(), 
			version = version + 1
		WHERE id = ANY($1) 
		  AND status = 'LOCKED';
	`
	_, err := r.db.Exec(ctx, query, ids)
	return err
}
