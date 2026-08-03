package service

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math/rand/v2"
	"net/http"
	"sort"
	"strings"
	"time"

	"github.com/google/uuid"
	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/booking-service/internal/repository"
	"github.com/ashishmor-17/showbook/apps/booking-service/internal/utils"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/clients"
)

var (
	ErrSeatAlreadyLocked  = errors.New("seats locks could not be acquired (already held)")
	ErrShowClosed         = errors.New("showtime is not open")
	ErrVenueUnavailable   = errors.New("venue service is unavailable")
	ErrInventoryTimeout   = errors.New("inventory service request timed out")
	ErrBookingNotFound    = errors.New("booking not found")
	ErrShowtimeNotFound   = errors.New("showtime not found")
	ErrForbiddenAccess    = errors.New("access denied")
	ErrIdempotencyConflict= errors.New("cannot replay request: hash mismatch or expired booking")
)

const DefaultConvenienceFeePaise = 2000

type VenueSeatResponse struct {
	SeatCode string `json:"seat_code"`
	Status   string `json:"status"`
}

type VenueRowResponse struct {
	Row   string              `json:"row"`
	Seats []VenueSeatResponse `json:"seats"`
}

type VenueCategorySeatsResponse struct {
	ID         uuid.UUID          `json:"id"`
	Name       string             `json:"name"`
	PricePaise int64              `json:"price_paise"`
	Rows       []VenueRowResponse `json:"rows"`
}

type VenueSeatMapResponse struct {
	ShowtimeID uuid.UUID                    `json:"showtime_id"`
	ScreenType string                       `json:"screen_type"`
	Status     string                       `json:"status"`
	Categories []VenueCategorySeatsResponse `json:"categories"`
}

type BookingService struct {
	repo                *repository.BookingRepository
	httpClient          *clients.HTTPClient
	venueServiceURL     string
	inventoryServiceURL string
	timeProvider        utils.TimeProvider
	log                 *zap.Logger
}

func NewBookingService(
	repo *repository.BookingRepository,
	httpClient *clients.HTTPClient,
	venueServiceURL string,
	inventoryServiceURL string,
	timeProvider utils.TimeProvider,
	log *zap.Logger,
) *BookingService {
	return &BookingService{
		repo:                repo,
		httpClient:          httpClient,
		venueServiceURL:     venueServiceURL,
		inventoryServiceURL: inventoryServiceURL,
		timeProvider:        timeProvider,
		log:                 log,
	}
}

func drainAndClose(body io.ReadCloser) {
	if body != nil {
		_, _ = io.Copy(io.Discard, body)
		body.Close()
	}
}

func calculateRequestHash(showtimeID string, seatCodes []string) string {
	sortedSeats := make([]string, len(seatCodes))
	copy(sortedSeats, seatCodes)
	sort.Strings(sortedSeats)

	h := sha256.New()
	h.Write([]byte(showtimeID))
	for _, code := range sortedSeats {
		h.Write([]byte(code))
	}
	return hex.EncodeToString(h.Sum(nil))
}

func (s *BookingService) InitiateBooking(
	ctx context.Context,
	correlationID string,
	userID string,
	showtimeID string,
	seatCodes []string,
	idempotencyKey *string,
) (*repository.Booking, error) {
	logger := s.log.With(
		zap.String("correlation_id", correlationID),
		zap.String("user_id", userID),
		zap.String("showtime_id", showtimeID),
	)

	if len(seatCodes) == 0 {
		return nil, errors.New("seat list cannot be empty")
	}
	if len(seatCodes) > 10 {
		return nil, errors.New("cannot lock more than 10 seats per booking")
	}
	userUUID, err := uuid.Parse(userID)
	if err != nil {
		return nil, fmt.Errorf("invalid user id uuid: %w", err)
	}
	showtimeUUID, err := uuid.Parse(showtimeID)
	if err != nil {
		return nil, fmt.Errorf("invalid showtime id uuid: %w", err)
	}
	if idempotencyKey != nil && len(*idempotencyKey) > 128 {
		return nil, errors.New("idempotency key is too long (max 128 chars)")
	}

	seen := make(map[string]bool)
	for _, code := range seatCodes {
		if seen[code] {
			return nil, fmt.Errorf("duplicate seat code '%s' in request", code)
		}
		seen[code] = true
	}

	requestHash := calculateRequestHash(showtimeID, seatCodes)

	// Check Idempotency Key
	if idempotencyKey != nil && *idempotencyKey != "" {
		existing, err := s.repo.CheckIdempotency(ctx, *idempotencyKey)
		if err != nil {
			return nil, fmt.Errorf("idempotency check failed: %w", err)
		}
		if existing != nil {
			if existing.UserID != userUUID || existing.RequestHash == nil || *existing.RequestHash != requestHash {
				return nil, ErrIdempotencyConflict
			}
			if existing.Status == utils.StatusExpired || existing.Status == utils.StatusCancelled {
				return nil, ErrIdempotencyConflict
			}
			logger.Info("Idempotent request replayed successfully", zap.String("booking_ref", existing.BookingRef))
			return existing, nil
		}
	}

	// Fetch Showtime Layout with retries
	venueURL := fmt.Sprintf("%s/api/v1/venues/showtimes/%s/seats", s.venueServiceURL, showtimeID)
	var resp *http.Response
	var cancelVenue context.CancelFunc
	backoff := 100 * time.Millisecond

	for retry := 0; retry < 3; retry++ {
		var venueCtx context.Context
		venueCtx, cancelVenue = context.WithTimeout(ctx, 2*time.Second)
		req, reqErr := http.NewRequestWithContext(venueCtx, "GET", venueURL, nil)
		if reqErr != nil {
			cancelVenue()
			return nil, fmt.Errorf("failed creating HTTP request: %w", reqErr)
		}

		resp, err = s.httpClient.Do(venueCtx, req)
		if err == nil && resp.StatusCode == http.StatusOK {
			break
		}

		cancelVenue()
		if resp != nil {
			drainAndClose(resp.Body)
		}

		jitter := time.Duration(rand.IntN(50)) * time.Millisecond
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(backoff + jitter):
		}
		backoff *= 2
	}
	if err != nil || resp == nil {
		if cancelVenue != nil {
			cancelVenue()
		}
		return nil, ErrVenueUnavailable
	}
	defer func() {
		drainAndClose(resp.Body)
		cancelVenue()
	}()

	if resp.StatusCode != http.StatusOK {
		if resp.StatusCode == http.StatusNotFound {
			return nil, ErrShowtimeNotFound
		}
		return nil, ErrVenueUnavailable
	}

	var seatMap VenueSeatMapResponse
	if err := json.NewDecoder(resp.Body).Decode(&seatMap); err != nil {
		return nil, fmt.Errorf("failed to parse layout response: %w", err)
	}

	if seatMap.Status != utils.ShowtimeStatusOpen {
		return nil, ErrShowClosed
	}

	seatMapLookup := make(map[string]struct {
		pricePaise   int64
		categoryName string
		status       string
	})
	for _, cat := range seatMap.Categories {
		for _, row := range cat.Rows {
			for _, seat := range row.Seats {
				seatMapLookup[seat.SeatCode] = struct {
					pricePaise   int64
					categoryName string
					status       string
				}{
					pricePaise:   cat.PricePaise,
					categoryName: cat.Name,
					status:       seat.Status,
				}
			}
		}
	}

	var totalAmountPaise int64
	var totalFeePaise int64
	var repoSeats []repository.BookingSeat
	bookingID := uuid.New()

	for _, code := range seatCodes {
		seatInfo, exists := seatMapLookup[code]
		if !exists {
			return nil, fmt.Errorf("seat %s does not exist in screen layout", code)
		}
		if seatInfo.status != "AVAILABLE" {
			return nil, fmt.Errorf("seat %s is no longer available (status: %s)", code, seatInfo.status)
		}

		totalAmountPaise += seatInfo.pricePaise
		totalFeePaise += DefaultConvenienceFeePaise

		repoSeats = append(repoSeats, repository.BookingSeat{
			ID:                  uuid.New(),
			BookingID:           bookingID,
			SeatCode:            code,
			SeatTypeName:        seatInfo.categoryName,
			UnitPricePaise:      seatInfo.pricePaise,
			ConvenienceFeePaise: DefaultConvenienceFeePaise,
		})
	}

	// Call inventory-service to lock seats
	inventoryURL := fmt.Sprintf("%s/api/v1/inventory/lock", s.inventoryServiceURL)
	var lockResp *http.Response
	var cancelInventory context.CancelFunc
	lockBackoff := 100 * time.Millisecond

	for retry := 0; retry < 3; retry++ {
		var inventoryCtx context.Context
		inventoryCtx, cancelInventory = context.WithTimeout(ctx, 2*time.Second)
		lockPayload := map[string]any{
			"showtime_id": showtimeID,
			"booking_id":  bookingID.String(),
			"seat_codes":  seatCodes,
		}
		bodyBytes, marshalErr := json.Marshal(lockPayload)
		if marshalErr != nil {
			cancelInventory()
			return nil, fmt.Errorf("failed to marshal lock request: %w", marshalErr)
		}

		lockReq, lockReqErr := http.NewRequestWithContext(inventoryCtx, "POST", inventoryURL, bytes.NewBuffer(bodyBytes))
		if lockReqErr != nil {
			cancelInventory()
			return nil, fmt.Errorf("failed to build lock request: %w", lockReqErr)
		}
		lockReq.Header.Set("Content-Type", "application/json")

		lockResp, err = s.httpClient.Do(inventoryCtx, lockReq)
		if err == nil && lockResp.StatusCode == http.StatusOK {
			break
		}

		cancelInventory()
		if lockResp != nil {
			drainAndClose(lockResp.Body)
		}

		jitter := time.Duration(rand.IntN(50)) * time.Millisecond
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(lockBackoff + jitter):
		}
		lockBackoff *= 2
	}
	if err != nil || lockResp == nil {
		if cancelInventory != nil {
			cancelInventory()
		}
		return nil, ErrInventoryTimeout
	}
	defer func() {
		drainAndClose(lockResp.Body)
		cancelInventory()
	}()

	if lockResp.StatusCode != http.StatusOK {
		return nil, ErrSeatAlreadyLocked
	}

	var lockRespBody struct {
		LockToken string `json:"lock_token"`
	}
	if decodeErr := json.NewDecoder(lockResp.Body).Decode(&lockRespBody); decodeErr != nil {
		s.log.Error("Failed to decode lock response body", zap.Error(decodeErr))
	}
	lockToken := lockRespBody.LockToken
	if lockToken == "" {
		lockToken = bookingID.String()
	}

	b := &repository.Booking{
		ID:                  bookingID,
		UserID:              userUUID,
		ShowtimeID:          showtimeUUID,
		Status:              utils.StatusInitiated,
		TotalAmountPaise:    totalAmountPaise,
		ConvenienceFeePaise: totalFeePaise,
		DiscountAmountPaise: 0,
		FinalAmountPaise:    totalAmountPaise + totalFeePaise,
		Currency:            "INR",
		ExpiresAt:           s.timeProvider.Now().Add(10 * time.Minute),
		IdempotencyKey:      idempotencyKey,
		RequestHash:         &requestHash,
		LockToken:           &lockToken,
	}

	event := &repository.OutboxEvent{
		ID:            uuid.New(),
		EventID:       uuid.New(),
		EventType:     utils.EventBookingInitiated,
		EventVersion:  1,
		AggregateType: "booking",
		AggregateID:   bookingID,
		Payload: map[string]any{
			"booking_id":   bookingID.String(),
			"booking_ref":  "",
			"user_id":      userID,
			"showtime_id":  showtimeID,
			"seat_codes":   seatCodes,
			"total_amount": b.FinalAmountPaise,
			"expires_at":   b.ExpiresAt.Format(time.RFC3339),
			"lock_token":   lockToken,
		},
	}

	var finalBookingRef string
	dbCtx, cancelDB := context.WithTimeout(ctx, 3*time.Second)
	defer cancelDB()

	dbSuccess := false
	for retry := 0; retry < 10; retry++ {
		select {
		case <-dbCtx.Done():
			err = dbCtx.Err()
		default:
			dateStr := s.timeProvider.Now().Format("20060102")
			finalBookingRef, err = utils.GenerateBookingRef(dateStr)
			if err != nil {
				s.QueueInventoryReleaseEvent(ctx, showtimeID, bookingID.String(), lockToken, seatCodes)
				return nil, fmt.Errorf("cryptographic random failure: %w", err)
			}

			b.BookingRef = finalBookingRef
			event.Payload.(map[string]any)["booking_ref"] = finalBookingRef

			err = s.repo.CreateBookingWithOutbox(dbCtx, b, repoSeats, event)
			if err == nil {
				dbSuccess = true
				break
			}
			
			if constraintName, isUnique := repository.GetUniqueViolationConstraint(err); isUnique {
				// Handle idempotency unique key collision (idx_bookings_idempotency)
				if constraintName == "idx_bookings_idempotency" {
					if idempotencyKey != nil && *idempotencyKey != "" {
						existing, checkErr := s.repo.CheckIdempotency(ctx, *idempotencyKey)
						if checkErr == nil && existing != nil {
							logger.Info("Concurrent request matched database idempotency key", zap.String("booking_ref", existing.BookingRef))
							s.QueueInventoryReleaseEvent(ctx, showtimeID, bookingID.String(), lockToken, seatCodes)
							return existing, nil
						}
					}
					break
				}
				
				// Handle booking ref unique key collision (bookings_booking_ref_key)
				if constraintName == "bookings_booking_ref_key" || strings.Contains(constraintName, "booking_ref") {
					logger.Warn("Booking ref collision occurred, retrying reference generation", zap.String("booking_ref", finalBookingRef))
					continue
				}
			}
		}
		break
	}

	if !dbSuccess {
		logger.Error("Failed saving booking. Queuing async release event", zap.Error(err))
		s.QueueInventoryReleaseEvent(ctx, showtimeID, bookingID.String(), lockToken, seatCodes)
		s.publishBookingFailedEvent(ctx, bookingID, finalBookingRef, userID, showtimeID, lockToken, seatCodes)
		return nil, fmt.Errorf("booking transaction failed: %w", err)
	}

	logger.Info("Booking initiated successfully", zap.String("booking_ref", finalBookingRef), zap.String("lock_token", lockToken))
	return b, nil
}

func (s *BookingService) QueueInventoryReleaseEvent(ctx context.Context, showtimeID, bookingID, lockToken string, seatCodes []string) {
	event := &repository.OutboxEvent{
		ID:            uuid.New(),
		EventID:       uuid.New(),
		EventType:     utils.EventInventoryReleaseRequested,
		EventVersion:  1,
		AggregateType: "booking",
		AggregateID:   uuid.MustParse(bookingID),
		Payload: map[string]any{
			"showtime_id": showtimeID,
			"booking_id":  bookingID,
			"lock_token":  lockToken,
			"seat_codes":  seatCodes,
		},
	}
	dbCtx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	if err := s.repo.InsertOutboxEventOnly(dbCtx, event); err != nil {
		s.log.Error("Failed queuing inventory release event to outbox", zap.Error(err))
	}
}

func (s *BookingService) publishBookingFailedEvent(ctx context.Context, id uuid.UUID, ref, user, showtime, lockToken string, seats []string) {
	event := &repository.OutboxEvent{
		ID:            uuid.New(),
		EventID:       uuid.New(),
		EventType:     utils.EventBookingFailed,
		EventVersion:  1,
		AggregateType: "booking",
		AggregateID:   id,
		Payload: map[string]any{
			"booking_id":  id.String(),
			"booking_ref": ref,
			"user_id":     user,
			"showtime_id": showtime,
			"seat_codes":  seats,
			"lock_token":  lockToken,
			"reason":      "database persistence transaction failure",
		},
	}
	dbCtx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	if err := s.repo.InsertOutboxEventOnly(dbCtx, event); err != nil {
		s.log.Error("Failed saving outbox event for booking failure", zap.Error(err))
	}
}

func (s *BookingService) GetBookingByRef(ctx context.Context, ref string) (*repository.Booking, []repository.BookingSeat, error) {
	return s.repo.GetBookingByRef(ctx, ref)
}

func (s *BookingService) ListBookings(ctx context.Context, userID string, cursor *time.Time, cursorID *uuid.UUID, limit int) ([]repository.Booking, error) {
	userUUID, err := uuid.Parse(userID)
	if err != nil {
		return nil, err
	}
	return s.repo.ListBookingsCursor(ctx, userUUID, cursor, cursorID, limit)
}
