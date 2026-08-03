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

	booking, err := h.svc.InitiateBooking(c.Request.Context(), correlationID, userID, req.ShowtimeID, req.SeatCodes, req.IdempotencyKey)
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

	response.Success(c, gin.H{
		"booking_id":   booking.ID.String(),
		"booking_ref":  booking.BookingRef,
		"status":       booking.Status,
		"seat_count":   len(req.SeatCodes),
		"total_amount": float64(booking.TotalAmountPaise) / 100.0,
		"final_amount": float64(booking.FinalAmountPaise) / 100.0,
		"currency":     booking.Currency,
		"expires_at":   booking.ExpiresAt.Format(time.RFC3339),
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
