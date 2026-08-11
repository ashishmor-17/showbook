package handlers

import (
	"errors"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/booking-service/internal/service"
	ginErrors "github.com/ashishmor-17/showbook/packages/go-lang/common/errors"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/response"
)

type BookingHandler struct {
	svc *service.BookingService
	log *zap.Logger
}

type seatItem struct {
	SeatCode       string  `json:"seat_code"`
	SeatType       string  `json:"seat_type"`
	Price          float64 `json:"price"`
	ConvenienceFee float64 `json:"convenience_fee"`
}

func NewBookingHandler(svc *service.BookingService, log *zap.Logger) *BookingHandler {
	return &BookingHandler{svc: svc, log: log}
}

type InitiateRequest struct {
	ShowtimeID     string   `json:"showtime_id" binding:"required,uuid"`
	SeatCodes      []string `json:"seat_codes" binding:"required,min=1"`
	IdempotencyKey *string  `json:"idempotency_key"`
}

func (h *BookingHandler) Initiate(c *gin.Context) {
	correlationID := c.GetString("correlation_id")
	userID := c.GetHeader("X-User-Id")
	if userID == "" {
		userID = c.Query("user_id")
		if userID == "" {
			c.Error(ginErrors.Unauthorized("MISSING_USER_ID", "User header required"))
			return
		}
	}

	var req InitiateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.Error(ginErrors.BadRequest("INVALID_REQUEST", err.Error()))
		return
	}

	booking, seats, err := h.svc.InitiateBooking(c.Request.Context(), correlationID, userID, req.ShowtimeID, req.SeatCodes, req.IdempotencyKey)
	if err != nil {
		h.log.Info("Booking initiation failed",
			zap.String("correlation_id", correlationID),
			zap.String("user_id", userID),
			zap.String("showtime_id", req.ShowtimeID),
			zap.Error(err),
		)

		switch {
		case errors.Is(err, service.ErrSeatAlreadyLocked) || errors.Is(err, service.ErrShowClosed):
			c.Error(ginErrors.Conflict("BOOKING_CONFLICT", err.Error()))
		case errors.Is(err, service.ErrVenueUnavailable) || errors.Is(err, service.ErrInventoryTimeout):
			c.Error(ginErrors.New(http.StatusServiceUnavailable, "SERVICE_UNAVAILABLE", err.Error()))
		case errors.Is(err, service.ErrShowtimeNotFound):
			c.Error(ginErrors.NotFound("SHOWTIME_NOT_FOUND", err.Error()))
		case errors.Is(err, service.ErrBookingNotFound):
			c.Error(ginErrors.NotFound("BOOKING_NOT_FOUND", err.Error()))
		case errors.Is(err, service.ErrIdempotencyConflict):
			c.Error(ginErrors.BadRequest("IDEMPOTENCY_CONFLICT", err.Error()))
		default:
			c.Error(ginErrors.BadRequest("INVALID_REQUEST", err.Error()))
		}
		return
	}

	var selectedSeats []seatItem
	for _, s := range seats {
		selectedSeats = append(selectedSeats, seatItem{
			SeatCode:       s.SeatCode,
			SeatType:       s.SeatTypeName,
			Price:          float64(s.UnitPricePaise) / 100.0,
			ConvenienceFee: float64(s.ConvenienceFeePaise) / 100.0,
		})
	}

	response.Success(c, gin.H{
		"booking_id":      booking.ID.String(),
		"booking_ref":     booking.BookingRef,
		"status":          booking.Status,
		"selected_seats":  selectedSeats,
		"subtotal":        float64(booking.TotalAmountPaise) / 100.0,
		"convenience_fee": float64(booking.ConvenienceFeePaise) / 100.0,
		"total":           float64(booking.FinalAmountPaise) / 100.0,
		"expires_at":      booking.ExpiresAt.Format(time.RFC3339),
	})
}

func (h *BookingHandler) Get(c *gin.Context) {
	ref := c.Param("booking_ref")
	userID := c.GetHeader("X-User-Id")
	if userID == "" {
		userID = c.Query("user_id")
		if userID == "" {
			c.Error(ginErrors.Unauthorized("MISSING_USER_ID", "User header required"))
			return
		}
	}

	booking, seats, err := h.svc.GetBookingByRef(c.Request.Context(), ref)
	if err != nil {
		c.Error(ginErrors.NotFound("BOOKING_NOT_FOUND", "Booking ref not found"))
		return
	}

	if booking.UserID.String() != userID {
		c.Error(ginErrors.New(http.StatusForbidden, "ACCESS_DENIED", "You are not authorized to view this booking"))
		return
	}

	var seatCodes []string
	for _, s := range seats {
		seatCodes = append(seatCodes, s.SeatCode)
	}

	response.Success(c, gin.H{
		"booking_id":   booking.ID.String(),
		"booking_ref":  booking.BookingRef,
		"status":       booking.Status,
		"seat_codes":   seatCodes,
		"total_amount": float64(booking.TotalAmountPaise) / 100.0,
		"final_amount": float64(booking.FinalAmountPaise) / 100.0,
		"currency":     booking.Currency,
		"expires_at":   booking.ExpiresAt.Format(time.RFC3339),
	})
}

func (h *BookingHandler) List(c *gin.Context) {
	userID := c.GetHeader("X-User-Id")
	if userID == "" {
		userID = c.Query("user_id")
		if userID == "" {
			c.Error(ginErrors.Unauthorized("MISSING_USER_ID", "User header required"))
			return
		}
	}

	var cursorTime *time.Time
	cursorStr := c.Query("cursor")
	if cursorStr != "" {
		t, err := time.Parse(time.RFC3339, cursorStr)
		if err == nil {
			cursorTime = &t
		}
	}

	var cursorID *uuid.UUID
	cursorIDStr := c.Query("cursor_id")
	if cursorIDStr != "" {
		uid, err := uuid.Parse(cursorIDStr)
		if err == nil {
			cursorID = &uid
		}
	}

	bookings, err := h.svc.ListBookings(c.Request.Context(), userID, cursorTime, cursorID, 20)
	if err != nil {
		c.Error(ginErrors.BadRequest("LIST_FAILED", err.Error()))
		return
	}

	var data []gin.H
	for _, b := range bookings {
		data = append(data, gin.H{
			"booking_ref":  b.BookingRef,
			"status":       b.Status,
			"final_amount": float64(b.FinalAmountPaise) / 100.0,
			"created_at":   b.CreatedAt.Format(time.RFC3339),
		})
	}

	var nextCursor string
	var nextCursorID string
	if len(bookings) == 20 {
		nextCursor = bookings[19].CreatedAt.Format(time.RFC3339)
		nextCursorID = bookings[19].ID.String()
	}

	response.Success(c, gin.H{
		"bookings":       data,
		"next_cursor":    nextCursor,
		"next_cursor_id": nextCursorID,
	})
}

func (h *BookingHandler) Cancel(c *gin.Context) {
	bookingRef := c.Param("booking_ref")
	if bookingRef == "" {
		c.Error(ginErrors.BadRequest("INVALID_BOOKING_REF", "Booking reference is required"))
		return
	}

	userID := c.GetHeader("X-User-Id")
	if userID == "" {
		userID = c.Query("user_id")
		if userID == "" {
			c.Error(ginErrors.Unauthorized("MISSING_USER_ID", "User header required"))
			return
		}
	}

	// Fetch booking to check authorization
	booking, _, err := h.svc.GetBookingByRef(c.Request.Context(), bookingRef)
	if err != nil {
		c.Error(ginErrors.NotFound("BOOKING_NOT_FOUND", "Booking not found"))
		return
	}

	if booking.UserID.String() != userID {
		c.Error(ginErrors.New(http.StatusForbidden, "ACCESS_DENIED", "You are not authorized to cancel this booking"))
		return
	}

	// Perform cancellation
	err = h.svc.CancelBooking(c.Request.Context(), booking.ID, "USER_REQUESTED", true)
	if err != nil {
		h.log.Error("Booking cancellation failed", zap.String("booking_ref", bookingRef), zap.Error(err))
		if err.Error() == "cannot cancel booking less than 2 hours before showtime" {
			c.Error(ginErrors.Conflict("CANCEL_FORBIDDEN", err.Error()))
			return
		}
		c.Error(ginErrors.BadRequest("CANCEL_FAILED", err.Error()))
		return
	}

	response.Success(c, gin.H{"message": "Booking cancelled successfully"})
}
