package repository

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/ashishmor-17/showbook/apps/booking-service/internal/utils"
)

type Booking struct {
	ID                       uuid.UUID
	BookingRef               string
	UserID                   uuid.UUID
	ShowtimeID               uuid.UUID
	Status                   string
	TotalAmountPaise         int64
	ConvenienceFeePaise      int64
	DiscountAmountPaise      int64
	FinalAmountPaise         int64
	Currency                 string
	ExpiresAt                time.Time
	IdempotencyKey           *string
	RequestHash              *string
	LockToken                *string
	PaymentID                *uuid.UUID
	PaymentProvider          *string
	PaymentProviderOrderID   *string
	PaymentProviderPaymentID *string
	CreatedAt                time.Time
	UpdatedAt                time.Time
}

type BookingSeat struct {
	ID                  uuid.UUID
	BookingID           uuid.UUID
	SeatCode            string
	SeatTypeName        string
	UnitPricePaise      int64
	ConvenienceFeePaise int64
}

type Ticket struct {
	ID        uuid.UUID
	BookingID uuid.UUID
	SeatCode  string
	Barcode   string
	Status    string
	IssuedAt  time.Time
}

type OutboxEvent struct {
	ID            uuid.UUID
	EventID       uuid.UUID
	EventType     string
	EventVersion  int
	AggregateType string
	AggregateID   uuid.UUID
	Payload       any
	RetryCount    int
	NextAttemptAt time.Time
}

type BookingRepository struct {
	db *pgxpool.Pool
}

func NewBookingRepository(db *pgxpool.Pool) *BookingRepository {
	return &BookingRepository{db: db}
}

// Check and return postgres constraint name for unique key violations
func GetUniqueViolationConstraint(err error) (string, bool) {
	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) {
		if pgErr.Code == "23505" {
			return pgErr.ConstraintName, true
		}
	}
	return "", false
}

func (r *BookingRepository) GetBookingByRef(ctx context.Context, ref string) (*Booking, []BookingSeat, error) {
	var b Booking
	err := r.db.QueryRow(ctx, `
		SELECT id, booking_ref, user_id, showtime_id, status, total_amount_paise, convenience_fee_paise, 
		       discount_amount_paise, final_amount_paise, currency, expires_at, idempotency_key, request_hash, lock_token,
		       payment_id, payment_provider, payment_provider_order_id, payment_provider_payment_id, created_at, updated_at
		FROM bookings WHERE booking_ref = $1`, ref).Scan(
		&b.ID, &b.BookingRef, &b.UserID, &b.ShowtimeID, &b.Status, &b.TotalAmountPaise, &b.ConvenienceFeePaise,
		&b.DiscountAmountPaise, &b.FinalAmountPaise, &b.Currency, &b.ExpiresAt, &b.IdempotencyKey, &b.RequestHash, &b.LockToken,
		&b.PaymentID, &b.PaymentProvider, &b.PaymentProviderOrderID, &b.PaymentProviderPaymentID, &b.CreatedAt, &b.UpdatedAt,
	)
	if err != nil {
		return nil, nil, err
	}

	rows, err := r.db.Query(ctx, `
		SELECT id, booking_id, seat_code, seat_type_name, unit_price_paise, convenience_fee_paise
		FROM booking_seats WHERE booking_id = $1`, b.ID)
	if err != nil {
		return nil, nil, err
	}
	defer rows.Close()

	var seats []BookingSeat
	for rows.Next() {
		var s BookingSeat
		if err := rows.Scan(&s.ID, &s.BookingID, &s.SeatCode, &s.SeatTypeName, &s.UnitPricePaise, &s.ConvenienceFeePaise); err != nil {
			return nil, nil, err
		}
		seats = append(seats, s)
	}
	if err = rows.Err(); err != nil {
		return nil, nil, err
	}

	return &b, seats, nil
}

// Fully populate all columns, including payment info, on idempotency checks
func (r *BookingRepository) CheckIdempotency(ctx context.Context, key string) (*Booking, error) {
	var b Booking
	err := r.db.QueryRow(ctx, `
		SELECT id, booking_ref, user_id, showtime_id, status, total_amount_paise, convenience_fee_paise, 
		       discount_amount_paise, final_amount_paise, currency, expires_at, idempotency_key, request_hash, lock_token,
		       payment_id, payment_provider, payment_provider_order_id, payment_provider_payment_id, created_at, updated_at
		FROM bookings WHERE idempotency_key = $1`, key).Scan(
		&b.ID, &b.BookingRef, &b.UserID, &b.ShowtimeID, &b.Status, &b.TotalAmountPaise, &b.ConvenienceFeePaise,
		&b.DiscountAmountPaise, &b.FinalAmountPaise, &b.Currency, &b.ExpiresAt, &b.IdempotencyKey, &b.RequestHash, &b.LockToken,
		&b.PaymentID, &b.PaymentProvider, &b.PaymentProviderOrderID, &b.PaymentProviderPaymentID, &b.CreatedAt, &b.UpdatedAt,
	)
	if err == pgx.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &b, nil
}

func (r *BookingRepository) CreateBookingWithOutbox(
	ctx context.Context,
	b *Booking,
	seats []BookingSeat,
	event *OutboxEvent,
) error {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback(ctx) }()

	_, err = tx.Exec(ctx, `
		INSERT INTO bookings (id, booking_ref, user_id, showtime_id, status, total_amount_paise, 
		                      convenience_fee_paise, discount_amount_paise, final_amount_paise, currency, expires_at, idempotency_key, request_hash, lock_token)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)`,
		b.ID, b.BookingRef, b.UserID, b.ShowtimeID, b.Status, b.TotalAmountPaise,
		b.ConvenienceFeePaise, b.DiscountAmountPaise, b.FinalAmountPaise, b.Currency, b.ExpiresAt, b.IdempotencyKey, b.RequestHash, b.LockToken,
	)
	if err != nil {
		return err
	}

	for _, s := range seats {
		_, err = tx.Exec(ctx, `
			INSERT INTO booking_seats (id, booking_id, seat_code, seat_type_name, unit_price_paise, convenience_fee_paise)
			VALUES ($1, $2, $3, $4, $5, $6)`,
			s.ID, s.BookingID, s.SeatCode, s.SeatTypeName, s.UnitPricePaise, s.ConvenienceFeePaise,
		)
		if err != nil {
			return err
		}
	}

	payloadJSON, err := json.Marshal(event.Payload)
	if err != nil {
		return err
	}

	_, err = tx.Exec(ctx, `
		INSERT INTO outbox (id, event_id, event_type, event_version, aggregate_type, aggregate_id, payload, status)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
		event.ID, event.EventID, event.EventType, event.EventVersion, event.AggregateType, event.AggregateID, payloadJSON, utils.OutboxStatusPending,
	)
	if err != nil {
		return err
	}

	return tx.Commit(ctx)
}

func (r *BookingRepository) InsertOutboxEventOnly(ctx context.Context, event *OutboxEvent) error {
	payloadJSON, err := json.Marshal(event.Payload)
	if err != nil {
		return err
	}
	_, err = r.db.Exec(ctx, `
		INSERT INTO outbox (id, event_id, event_type, event_version, aggregate_type, aggregate_id, payload, status)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
		event.ID, event.EventID, event.EventType, event.EventVersion, event.AggregateType, event.AggregateID, payloadJSON, utils.OutboxStatusPending,
	)
	return err
}

func (r *BookingRepository) FetchAndLockOutbox(ctx context.Context, limit int) ([]*OutboxEvent, error) {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return nil, err
	}
	defer func() { _ = tx.Rollback(ctx) }()

	rows, err := tx.Query(ctx, `
		WITH locked_events AS (
			SELECT id 
			FROM outbox 
			WHERE status = $1 AND next_attempt_at <= NOW()
			ORDER BY created_at ASC 
			LIMIT $2 
			FOR UPDATE SKIP LOCKED
		)
		UPDATE outbox 
		SET status = $3
		FROM locked_events 
		WHERE outbox.id = locked_events.id
		RETURNING outbox.id, outbox.event_id, outbox.event_type, outbox.event_version, outbox.aggregate_type, outbox.aggregate_id, outbox.payload, outbox.retry_count`,
		utils.OutboxStatusPending, limit, utils.OutboxStatusProcessing)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var events []*OutboxEvent
	for rows.Next() {
		var e OutboxEvent
		var rawPayload []byte
		if err := rows.Scan(&e.ID, &e.EventID, &e.EventType, &e.EventVersion, &e.AggregateType, &e.AggregateID, &rawPayload, &e.RetryCount); err != nil {
			return nil, err
		}
		var payloadMap map[string]any
		if err := json.Unmarshal(rawPayload, &payloadMap); err != nil {
			return nil, err
		}
		e.Payload = payloadMap
		events = append(events, &e)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	if err := tx.Commit(ctx); err != nil {
		return nil, err
	}

	return events, nil
}

func (r *BookingRepository) UpdateOutboxStatus(ctx context.Context, event *OutboxEvent, status string) error {
	if status == "FAILED" {
		if event.RetryCount >= 10 {
			_, err := r.db.Exec(ctx, `UPDATE outbox SET status = $1, retry_count = retry_count + 1 WHERE id = $2`, utils.OutboxStatusDead, event.ID)
			return err
		}
		delaySeconds := 1 << event.RetryCount
		nextAttempt := time.Now().Add(time.Duration(delaySeconds) * time.Second)

		_, err := r.db.Exec(ctx, `UPDATE outbox SET status = $1, retry_count = retry_count + 1, next_attempt_at = $2 WHERE id = $3`,
			utils.OutboxStatusPending, nextAttempt, event.ID)
		return err
	}
	_, err := r.db.Exec(ctx, `UPDATE outbox SET status = $1, published_at = NOW() WHERE id = $2`, utils.OutboxStatusPublished, event.ID)
	return err
}

func (r *BookingRepository) GetBookingByID(ctx context.Context, id uuid.UUID) (*Booking, []BookingSeat, error) {
	var b Booking
	err := r.db.QueryRow(ctx, `
		SELECT id, booking_ref, user_id, showtime_id, status, total_amount_paise, convenience_fee_paise, 
		       discount_amount_paise, final_amount_paise, currency, expires_at, idempotency_key, request_hash, lock_token,
		       payment_id, payment_provider, payment_provider_order_id, payment_provider_payment_id, created_at, updated_at
		FROM bookings WHERE id = $1`, id).Scan(
		&b.ID, &b.BookingRef, &b.UserID, &b.ShowtimeID, &b.Status, &b.TotalAmountPaise, &b.ConvenienceFeePaise,
		&b.DiscountAmountPaise, &b.FinalAmountPaise, &b.Currency, &b.ExpiresAt, &b.IdempotencyKey, &b.RequestHash, &b.LockToken,
		&b.PaymentID, &b.PaymentProvider, &b.PaymentProviderOrderID, &b.PaymentProviderPaymentID, &b.CreatedAt, &b.UpdatedAt,
	)
	if err != nil {
		return nil, nil, err
	}

	rows, err := r.db.Query(ctx, `
		SELECT id, booking_id, seat_code, seat_type_name, unit_price_paise, convenience_fee_paise
		FROM booking_seats WHERE booking_id = $1`, b.ID)
	if err != nil {
		return nil, nil, err
	}
	defer rows.Close()

	var seats []BookingSeat
	for rows.Next() {
		var s BookingSeat
		if err := rows.Scan(&s.ID, &s.BookingID, &s.SeatCode, &s.SeatTypeName, &s.UnitPricePaise, &s.ConvenienceFeePaise); err != nil {
			return nil, nil, err
		}
		seats = append(seats, s)
	}
	if err = rows.Err(); err != nil {
		return nil, nil, err
	}

	return &b, seats, nil
}

func (r *BookingRepository) ConfirmBookingWithOutbox(
	ctx context.Context,
	bookingID uuid.UUID,
	paymentID uuid.UUID,
	gateway string,
	gatewayTxnID string,
	tickets []Ticket,
	event *OutboxEvent,
) error {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback(ctx) }()

	res, err := tx.Exec(ctx, `
		UPDATE bookings 
		SET status = $1, payment_id = $2, payment_provider = $3, payment_provider_payment_id = $4, updated_at = NOW() 
		WHERE id = $5 AND status = $6`,
		utils.StatusConfirmed, paymentID, gateway, gatewayTxnID, bookingID, utils.StatusInitiated,
	)
	if err != nil {
		return err
	}
	if res.RowsAffected() == 0 {
		return errors.New("booking is not in INITIATED status or already updated")
	}

	for _, t := range tickets {
		_, err = tx.Exec(ctx, `
			INSERT INTO tickets (id, booking_id, seat_code, barcode, status, issued_at)
			VALUES ($1, $2, $3, $4, $5, NOW())`,
			t.ID, t.BookingID, t.SeatCode, t.Barcode, t.Status,
		)
		if err != nil {
			return err
		}
	}

	payloadJSON, err := json.Marshal(event.Payload)
	if err != nil {
		return err
	}

	_, err = tx.Exec(ctx, `
		INSERT INTO outbox (id, event_id, event_type, event_version, aggregate_type, aggregate_id, payload, status)
		VALUES ($1, $2, $3, 1, 'booking', $4, $5, $6)`,
		event.ID, event.EventID, event.EventType, bookingID, payloadJSON, utils.OutboxStatusPending,
	)
	if err != nil {
		return err
	}

	return tx.Commit(ctx)
}

func (r *BookingRepository) CancelBookingWithOutbox(
	ctx context.Context,
	bookingID uuid.UUID,
	cancelEvent *OutboxEvent,
	releaseEvent *OutboxEvent,
) error {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback(ctx) }()

	res, err := tx.Exec(ctx, `
		UPDATE bookings 
		SET status = $1, updated_at = NOW() 
		WHERE id = $2 AND status IN ($3, $4)`,
		utils.StatusCancelled, bookingID, utils.StatusInitiated, utils.StatusConfirmed,
	)
	if err != nil {
		return err
	}
	if res.RowsAffected() == 0 {
		return errors.New("booking status could not be transitioned to CANCELLED")
	}

	cancelPayloadJSON, err := json.Marshal(cancelEvent.Payload)
	if err != nil {
		return err
	}
	_, err = tx.Exec(ctx, `
		INSERT INTO outbox (id, event_id, event_type, event_version, aggregate_type, aggregate_id, payload, status)
		VALUES ($1, $2, $3, 1, 'booking', $4, $5, $6)`,
		cancelEvent.ID, cancelEvent.EventID, cancelEvent.EventType, bookingID, cancelPayloadJSON, utils.OutboxStatusPending,
	)
	if err != nil {
		return err
	}

	if releaseEvent != nil {
		releasePayloadJSON, err := json.Marshal(releaseEvent.Payload)
		if err != nil {
			return err
		}
		_, err = tx.Exec(ctx, `
			INSERT INTO outbox (id, event_id, event_type, event_version, aggregate_type, aggregate_id, payload, status)
			VALUES ($1, $2, $3, 1, 'booking', $4, $5, $6)`,
			releaseEvent.ID, releaseEvent.EventID, releaseEvent.EventType, bookingID, releasePayloadJSON, utils.OutboxStatusPending,
		)
		if err != nil {
			return err
		}
	}

	return tx.Commit(ctx)
}

func (r *BookingRepository) ExpireBookingsBulk(ctx context.Context, limit int) ([]Booking, [][]string, error) {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return nil, nil, err
	}
	defer func() { _ = tx.Rollback(ctx) }()

	rows, err := tx.Query(ctx, `
		WITH target_bookings AS (
			SELECT id 
			FROM bookings 
			WHERE status = $1 AND expires_at < NOW()
			LIMIT $2
			FOR UPDATE SKIP LOCKED
		),
		aggregated_seats AS (
			SELECT booking_id, ARRAY_TO_STRING(ARRAY_AGG(seat_code), ',') as seats
			FROM booking_seats
			WHERE booking_id IN (SELECT id FROM target_bookings)
			GROUP BY booking_id
		),
		updated_bookings AS (
			UPDATE bookings
			SET status = $3, updated_at = NOW()
			WHERE id IN (SELECT id FROM target_bookings)
			RETURNING id, booking_ref, showtime_id, lock_token
		)
		SELECT b.id, b.booking_ref, b.showtime_id, b.lock_token, COALESCE(s.seats, '')
		FROM updated_bookings b
		LEFT JOIN aggregated_seats s ON b.id = s.booking_id`,
		utils.StatusInitiated, limit, utils.StatusExpired)
	if err != nil {
		return nil, nil, err
	}
	defer rows.Close()

	var expired []Booking
	var expiredSeats [][]string

	for rows.Next() {
		var b Booking
		var seatsJoined string
		if err := rows.Scan(&b.ID, &b.BookingRef, &b.ShowtimeID, &b.LockToken, &seatsJoined); err != nil {
			return nil, nil, err
		}
		expired = append(expired, b)

		var seatCodes []string
		if seatsJoined != "" {
			seatCodes = strings.Split(seatsJoined, ",")
		}
		expiredSeats = append(expiredSeats, seatCodes)
	}

	if err = rows.Err(); err != nil {
		return nil, nil, err
	}

	if len(expired) == 0 {
		return nil, nil, nil
	}

	for i, b := range expired {
		seatCodes := expiredSeats[i]

		expiredPayload := map[string]any{
			"booking_id":  b.ID.String(),
			"booking_ref": b.BookingRef,
			"showtime_id": b.ShowtimeID.String(),
			"seat_codes":  seatCodes,
			"reason":      "payment deadline exceeded",
		}
		payloadBytes, err := json.Marshal(expiredPayload)
		if err != nil {
			return nil, nil, err
		}

		_, err = tx.Exec(ctx, `
			INSERT INTO outbox (id, event_id, event_type, event_version, aggregate_type, aggregate_id, payload, status)
			VALUES ($1, $2, $3, 1, 'booking', $4, $5, $6)`,
			uuid.New(), uuid.New(), utils.EventBookingExpired, b.ID, payloadBytes, utils.OutboxStatusPending,
		)
		if err != nil {
			return nil, nil, err
		}

		lockTokenVal := ""
		if b.LockToken != nil {
			lockTokenVal = *b.LockToken
		}

		releasePayload := map[string]any{
			"showtime_id": b.ShowtimeID.String(),
			"booking_id":  b.ID.String(),
			"lock_token":  lockTokenVal,
			"seat_codes":  seatCodes,
		}
		releaseBytes, err := json.Marshal(releasePayload)
		if err != nil {
			return nil, nil, err
		}

		_, err = tx.Exec(ctx, `
			INSERT INTO outbox (id, event_id, event_type, event_version, aggregate_type, aggregate_id, payload, status)
			VALUES ($1, $2, $3, 1, 'booking', $4, $5, $6)`,
			uuid.New(), uuid.New(), utils.EventInventoryReleaseRequested, b.ID, releaseBytes, utils.OutboxStatusPending,
		)
		if err != nil {
			return nil, nil, err
		}
	}

	if err := tx.Commit(ctx); err != nil {
		return nil, nil, err
	}

	return expired, expiredSeats, nil
}

func (r *BookingRepository) ListBookingsCursor(ctx context.Context, userID uuid.UUID, cursor *time.Time, cursorID *uuid.UUID, limit int) ([]Booking, error) {
	var rows pgx.Rows
	var err error
	if cursor == nil || cursorID == nil {
		rows, err = r.db.Query(ctx, `
			SELECT id, booking_ref, user_id, showtime_id, status, total_amount_paise, convenience_fee_paise, 
			       discount_amount_paise, final_amount_paise, currency, expires_at, created_at, updated_at
			FROM bookings 
			WHERE user_id = $1 
			ORDER BY created_at DESC, id DESC 
			LIMIT $2`, userID, limit)
	} else {
		rows, err = r.db.Query(ctx, `
			SELECT id, booking_ref, user_id, showtime_id, status, total_amount_paise, convenience_fee_paise, 
			       discount_amount_paise, final_amount_paise, currency, expires_at, created_at, updated_at
			FROM bookings 
			WHERE user_id = $1 AND (created_at < $2 OR (created_at = $2 AND id < $3))
			ORDER BY created_at DESC, id DESC 
			LIMIT $4`, userID, *cursor, *cursorID, limit)
	}
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var bookings []Booking
	for rows.Next() {
		var b Booking
		err := rows.Scan(
			&b.ID, &b.BookingRef, &b.UserID, &b.ShowtimeID, &b.Status, &b.TotalAmountPaise, &b.ConvenienceFeePaise,
			&b.DiscountAmountPaise, &b.FinalAmountPaise, &b.Currency, &b.ExpiresAt, &b.CreatedAt, &b.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		bookings = append(bookings, b)
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}

	return bookings, nil
}
