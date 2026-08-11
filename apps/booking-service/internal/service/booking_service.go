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
	"github.com/jackc/pgx/v5"
	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/booking-service/internal/repository"
	"github.com/ashishmor-17/showbook/apps/booking-service/internal/utils"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/clients"
)

var (
	ErrSeatAlreadyLocked   = errors.New("seats locks could not be acquired (already held)")
	ErrShowClosed          = errors.New("showtime is not open")
	ErrVenueUnavailable    = errors.New("venue service is unavailable")
	ErrInventoryTimeout    = errors.New("inventory service request timed out")
	ErrBookingNotFound     = errors.New("booking not found")
	ErrShowtimeNotFound    = errors.New("showtime not found")
	ErrForbiddenAccess     = errors.New("access denied")
	ErrIdempotencyConflict = errors.New("cannot replay request: hash mismatch or expired booking")
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
	catalogServiceURL   string
	userServiceURL      string
	timeProvider        utils.TimeProvider
	log                 *zap.Logger
}

func NewBookingService(
	repo *repository.BookingRepository,
	httpClient *clients.HTTPClient,
	venueServiceURL string,
	inventoryServiceURL string,
	catalogServiceURL string,
	userServiceURL string,
	timeProvider utils.TimeProvider,
	log *zap.Logger,
) *BookingService {
	return &BookingService{
		repo:                repo,
		httpClient:          httpClient,
		venueServiceURL:     venueServiceURL,
		inventoryServiceURL: inventoryServiceURL,
		catalogServiceURL:   catalogServiceURL,
		userServiceURL:      userServiceURL,
		timeProvider:        timeProvider,
		log:                 log,
	}
}

type UserProfile struct {
	UserID uuid.UUID `json:"user_id"`
	Email  string    `json:"email"`
	Name   string    `json:"name"`
	Phone  string    `json:"phone"`
}

func (s *BookingService) fetchUserProfile(ctx context.Context, userID string) (*UserProfile, error) {
	url := fmt.Sprintf("%s/api/internal/users/%s", s.userServiceURL, userID)
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("X-Internal-Service", "true")

	resp, err := s.httpClient.Do(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed calling user-service: %w", err)
	}
	defer drainAndClose(resp.Body)

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed fetching user details (status %d)", resp.StatusCode)
	}

	var profile UserProfile
	if err := json.NewDecoder(resp.Body).Decode(&profile); err != nil {
		return nil, err
	}
	return &profile, nil
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
) (*repository.Booking, []repository.BookingSeat, error) {
	logger := s.log.With(
		zap.String("correlation_id", correlationID),
		zap.String("user_id", userID),
		zap.String("showtime_id", showtimeID),
	)

	if len(seatCodes) == 0 {
		return nil, nil, errors.New("seat list cannot be empty")
	}
	if len(seatCodes) > 10 {
		return nil, nil, errors.New("cannot lock more than 10 seats per booking")
	}
	userUUID, err := uuid.Parse(userID)
	if err != nil {
		return nil, nil, fmt.Errorf("invalid user id uuid: %w", err)
	}
	showtimeUUID, err := uuid.Parse(showtimeID)
	if err != nil {
		return nil, nil, fmt.Errorf("invalid showtime id uuid: %w", err)
	}
	if idempotencyKey != nil && len(*idempotencyKey) > 128 {
		return nil, nil, errors.New("idempotency key is too long (max 128 chars)")
	}

	seen := make(map[string]bool)
	for _, code := range seatCodes {
		if seen[code] {
			return nil, nil, fmt.Errorf("duplicate seat code '%s' in request", code)
		}
		seen[code] = true
	}

	requestHash := calculateRequestHash(showtimeID, seatCodes)

	// Check Idempotency Key
	if idempotencyKey != nil && *idempotencyKey != "" {
		existing, err := s.repo.CheckIdempotency(ctx, *idempotencyKey)
		if err != nil {
			return nil, nil, fmt.Errorf("idempotency check failed: %w", err)
		}
		if existing != nil {
			if existing.UserID != userUUID || existing.RequestHash == nil || *existing.RequestHash != requestHash {
				return nil, nil, ErrIdempotencyConflict
			}
			if existing.Status == utils.StatusExpired || existing.Status == utils.StatusCancelled {
				return nil, nil, ErrIdempotencyConflict
			}
			logger.Info("Idempotent request replayed successfully", zap.String("booking_ref", existing.BookingRef))
			_, seats, getErr := s.repo.GetBookingByRef(ctx, existing.BookingRef)
			if getErr != nil {
				return existing, nil, nil
			}
			return existing, seats, nil
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
			return nil, nil, fmt.Errorf("failed creating HTTP request: %w", reqErr)
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
			return nil, nil, ctx.Err()
		case <-time.After(backoff + jitter):
		}
		backoff *= 2
	}
	if err != nil || resp == nil {
		if cancelVenue != nil {
			cancelVenue()
		}
		return nil, nil, ErrVenueUnavailable
	}
	defer func() {
		drainAndClose(resp.Body)
		cancelVenue()
	}()

	if resp.StatusCode != http.StatusOK {
		if resp.StatusCode == http.StatusNotFound {
			return nil, nil, ErrShowtimeNotFound
		}
		return nil, nil, ErrVenueUnavailable
	}

	var seatMap VenueSeatMapResponse
	if err := json.NewDecoder(resp.Body).Decode(&seatMap); err != nil {
		return nil, nil, fmt.Errorf("failed to parse layout response: %w", err)
	}

	if seatMap.Status != utils.ShowtimeStatusOpen {
		return nil, nil, ErrShowClosed
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
			return nil, nil, fmt.Errorf("seat %s does not exist in screen layout", code)
		}
		if seatInfo.status != "AVAILABLE" {
			return nil, nil, fmt.Errorf("seat %s is no longer available (status: %s)", code, seatInfo.status)
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
			return nil, nil, fmt.Errorf("failed to marshal lock request: %w", marshalErr)
		}

		lockReq, lockReqErr := http.NewRequestWithContext(inventoryCtx, "POST", inventoryURL, bytes.NewBuffer(bodyBytes))
		if lockReqErr != nil {
			cancelInventory()
			return nil, nil, fmt.Errorf("failed to build lock request: %w", lockReqErr)
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
			return nil, nil, ctx.Err()
		case <-time.After(lockBackoff + jitter):
		}
		lockBackoff *= 2
	}
	if err != nil || lockResp == nil {
		if cancelInventory != nil {
			cancelInventory()
		}
		return nil, nil, ErrInventoryTimeout
	}
	defer func() {
		drainAndClose(lockResp.Body)
		cancelInventory()
	}()

	if lockResp.StatusCode != http.StatusOK {
		return nil, nil, ErrSeatAlreadyLocked
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

	var userEmail, userName, userPhone string
	if profile, profileErr := s.fetchUserProfile(ctx, userID); profileErr == nil {
		userEmail = profile.Email
		userName = profile.Name
		userPhone = profile.Phone
	} else {
		s.log.Warn("Failed to fetch user profile for booking initiation", zap.String("user_id", userID), zap.Error(profileErr))
		userName = "Customer"
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
			"user_email":   userEmail,
			"user_name":    userName,
			"user_phone":   userPhone,
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
				return nil, nil, fmt.Errorf("cryptographic random failure: %w", err)
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
							return existing, nil, nil
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
		return nil, nil, fmt.Errorf("booking transaction failed: %w", err)
	}

	logger.Info("Booking initiated successfully", zap.String("booking_ref", finalBookingRef), zap.String("lock_token", lockToken))
	return b, repoSeats, nil
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
	dbCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
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

func (s *BookingService) GetBookingByID(ctx context.Context, id uuid.UUID) (*repository.Booking, []repository.BookingSeat, error) {
	return s.repo.GetBookingByID(ctx, id)
}

func (s *BookingService) ConfirmBooking(
	ctx context.Context,
	bookingRef string,
	paymentID uuid.UUID,
	gateway string,
	gatewayTxnID string,
) error {
	s.log.Info("Confirming booking", zap.String("booking_ref", bookingRef), zap.String("payment_id", paymentID.String()))

	// Fetch booking with seats
	booking, seats, err := s.repo.GetBookingByRef(ctx, bookingRef)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return ErrBookingNotFound
		}
		return err
	}

	// Idempotency check
	if booking.Status == utils.StatusConfirmed {
		s.log.Info("Booking already confirmed", zap.String("booking_ref", bookingRef))
		return nil
	}

	// Call inventory service to confirm seats
	inventoryURL := fmt.Sprintf("%s/api/v1/inventory/confirm", s.inventoryServiceURL)
	seatCodes := make([]string, len(seats))
	for i, seat := range seats {
		seatCodes[i] = seat.SeatCode
	}

	confirmPayload := map[string]any{
		"showtime_id": booking.ShowtimeID.String(),
		"booking_id":  booking.ID.String(),
		"seat_codes":  seatCodes,
	}

	bodyBytes, err := json.Marshal(confirmPayload)
	if err != nil {
		return err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", inventoryURL, bytes.NewBuffer(bodyBytes))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := s.httpClient.Do(ctx, req)
	if err != nil {
		return fmt.Errorf("failed calling inventory-service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("failed inventory confirmation (status %d): %s", resp.StatusCode, string(body))
	}

	// Fetch Showtime Details (venue_name, movie_id, show_date, start_time)
	venueURL := fmt.Sprintf("%s/api/v1/venues/showtimes/%s", s.venueServiceURL, booking.ShowtimeID.String())
	venueReq, err := http.NewRequestWithContext(ctx, "GET", venueURL, nil)
	if err != nil {
		return err
	}
	venueResp, err := s.httpClient.Do(ctx, venueReq)
	if err != nil {
		return fmt.Errorf("failed calling venue-service: %w", err)
	}
	defer venueResp.Body.Close()

	if venueResp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed fetching showtime details from venue-service (status %d)", venueResp.StatusCode)
	}

	var showtimeDetails struct {
		VenueName string `json:"venue_name"`
		MovieID   string `json:"movie_id"`
		ShowDate  string `json:"show_date"`
		StartTime string `json:"start_time"`
	}
	if err := json.NewDecoder(venueResp.Body).Decode(&showtimeDetails); err != nil {
		return err
	}

	// Fetch Movie Details (movie_title)
	catalogURL := fmt.Sprintf("%s/api/v1/catalog/movies/id/%s", s.catalogServiceURL, showtimeDetails.MovieID)
	catalogReq, err := http.NewRequestWithContext(ctx, "GET", catalogURL, nil)
	if err != nil {
		return err
	}
	catalogResp, err := s.httpClient.Do(ctx, catalogReq)
	if err != nil {
		return fmt.Errorf("failed calling catalog-service: %w", err)
	}
	defer catalogResp.Body.Close()

	if catalogResp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed fetching movie details from catalog-service (status %d)", catalogResp.StatusCode)
	}

	var movieDetails struct {
		Title string `json:"title"`
	}
	if err := json.NewDecoder(catalogResp.Body).Decode(&movieDetails); err != nil {
		return err
	}

	// Generate unique barcode and Ticket records
	var tickets []repository.Ticket
	var eventTickets []map[string]any
	for _, seat := range seats {
		barcode := fmt.Sprintf("TKT-%s-%s", booking.BookingRef, seat.SeatCode)
		tickets = append(tickets, repository.Ticket{
			ID:        uuid.New(),
			BookingID: booking.ID,
			SeatCode:  seat.SeatCode,
			Barcode:   barcode,
			Status:    "VALID",
		})
		eventTickets = append(eventTickets, map[string]any{
			"seat_code": seat.SeatCode,
			"barcode":   barcode,
		})
	}

	// Build the booking.confirmed outbox event
	var userEmail, userName, userPhone string
	if profile, profileErr := s.fetchUserProfile(ctx, booking.UserID.String()); profileErr == nil {
		userEmail = profile.Email
		userName = profile.Name
		userPhone = profile.Phone
	} else {
		s.log.Warn("Failed to fetch user profile for booking confirmation", zap.String("user_id", booking.UserID.String()), zap.Error(profileErr))
		userName = "Customer"
	}

	event := &repository.OutboxEvent{
		ID:            uuid.New(),
		EventID:       uuid.New(),
		EventType:     utils.EventBookingConfirmed,
		EventVersion:  1,
		AggregateType: "booking",
		AggregateID:   booking.ID,
		Payload: map[string]any{
			"booking_ref":  booking.BookingRef,
			"user_id":      booking.UserID.String(),
			"user_email":   userEmail,
			"user_name":    userName,
			"user_phone":   userPhone,
			"showtime_id":  booking.ShowtimeID.String(),
			"movie_title":  movieDetails.Title,
			"venue_name":   showtimeDetails.VenueName,
			"show_date":    showtimeDetails.ShowDate,
			"start_time":   showtimeDetails.StartTime,
			"seat_codes":   seatCodes,
			"total_amount": float64(booking.FinalAmountPaise) / 100.0,
			"tickets":      eventTickets,
		},
	}

	// Commit changes to Database
	err = s.repo.ConfirmBookingWithOutbox(ctx, booking.ID, paymentID, gateway, gatewayTxnID, tickets, event)
	if err != nil {
		return fmt.Errorf("db transaction for confirm booking failed: %w", err)
	}

	s.log.Info("Booking confirmed successfully", zap.String("booking_ref", bookingRef))
	return nil
}

func (s *BookingService) CancelBooking(
	ctx context.Context,
	bookingID uuid.UUID,
	reason string,
	isUserCancelled bool,
) error {
	s.log.Info("Cancelling booking", zap.String("booking_id", bookingID.String()), zap.String("reason", reason))

	// Fetch booking with seats
	booking, seats, err := s.repo.GetBookingByID(ctx, bookingID)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return ErrBookingNotFound
		}
		return err
	}

	// Idempotency check
	if booking.Status == utils.StatusCancelled {
		s.log.Info("Booking already cancelled", zap.String("booking_id", bookingID.String()))
		return nil
	}

	// If user initiated cancellation, check if show starts in < 2 hours
	if isUserCancelled {
		venueURL := fmt.Sprintf("%s/api/v1/venues/showtimes/%s", s.venueServiceURL, booking.ShowtimeID.String())
		venueReq, err := http.NewRequestWithContext(ctx, "GET", venueURL, nil)
		if err != nil {
			return err
		}
		venueResp, err := s.httpClient.Do(ctx, venueReq)
		if err != nil {
			return fmt.Errorf("failed calling venue-service: %w", err)
		}
		defer venueResp.Body.Close()

		if venueResp.StatusCode != http.StatusOK {
			return fmt.Errorf("failed fetching showtime details from venue-service (status %d)", venueResp.StatusCode)
		}

		var showtimeDetails struct {
			StartDatetime string `json:"start_datetime"`
		}
		if err := json.NewDecoder(venueResp.Body).Decode(&showtimeDetails); err != nil {
			return err
		}

		startDT, err := time.Parse(time.RFC3339, showtimeDetails.StartDatetime)
		if err != nil {
			startDT, err = time.Parse("2006-01-02T15:04:05", showtimeDetails.StartDatetime)
		}
		if err != nil {
			return fmt.Errorf("failed to parse start datetime: %w", err)
		}

		if startDT.Sub(s.timeProvider.Now()) < 2*time.Hour {
			return errors.New("cannot cancel booking less than 2 hours before showtime")
		}
	}

	// Build booking.cancelled outbox event
	seatCodes := make([]string, len(seats))
	for i, seat := range seats {
		seatCodes[i] = seat.SeatCode
	}

	refundEligible := false
	if booking.Status == utils.StatusConfirmed {
		refundEligible = true
	}

	var userEmail, userName, userPhone string
	if profile, profileErr := s.fetchUserProfile(ctx, booking.UserID.String()); profileErr == nil {
		userEmail = profile.Email
		userName = profile.Name
		userPhone = profile.Phone
	} else {
		s.log.Warn("Failed to fetch user profile for booking cancellation", zap.String("user_id", booking.UserID.String()), zap.Error(profileErr))
		userName = "Customer"
	}

	cancelEvent := &repository.OutboxEvent{
		ID:            uuid.New(),
		EventID:       uuid.New(),
		EventType:     utils.EventBookingCancelled,
		EventVersion:  1,
		AggregateType: "booking",
		AggregateID:   booking.ID,
		Payload: map[string]any{
			"booking_ref":         booking.BookingRef,
			"user_id":             booking.UserID.String(),
			"user_email":          userEmail,
			"user_name":           userName,
			"user_phone":          userPhone,
			"showtime_id":         booking.ShowtimeID.String(),
			"seat_codes":          seatCodes,
			"cancellation_reason": reason,
			"refund_eligible":     refundEligible,
			"refund_amount":       float64(booking.FinalAmountPaise) / 100.0,
		},
	}

	// Build inventory.release.requested outbox event
	lockTokenVal := ""
	if booking.LockToken != nil {
		lockTokenVal = *booking.LockToken
	}
	releaseEvent := &repository.OutboxEvent{
		ID:            uuid.New(),
		EventID:       uuid.New(),
		EventType:     utils.EventInventoryReleaseRequested,
		EventVersion:  1,
		AggregateType: "booking",
		AggregateID:   booking.ID,
		Payload: map[string]any{
			"showtime_id": booking.ShowtimeID.String(),
			"booking_id":  booking.ID.String(),
			"lock_token":  lockTokenVal,
			"seat_codes":  seatCodes,
		},
	}

	// Update DB inside a transaction
	err = s.repo.CancelBookingWithOutbox(ctx, booking.ID, cancelEvent, releaseEvent)
	if err != nil {
		return fmt.Errorf("db transaction for cancel booking failed: %w", err)
	}

	s.log.Info("Booking cancelled successfully", zap.String("booking_id", bookingID.String()))
	return nil
}
