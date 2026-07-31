package handlers

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/inventory-service/internal/service"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/errors"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/response"
)

type InventoryHandler struct {
	svc *service.InventoryService
	log *zap.Logger
}

func NewInventoryHandler(svc *service.InventoryService, log *zap.Logger) *InventoryHandler {
	return &InventoryHandler{svc: svc, log: log}
}

type LockRequest struct {
	ShowtimeID string   `json:"showtime_id" binding:"required,uuid"`
	BookingID  string   `json:"booking_id" binding:"required,uuid"`
	SeatCodes  []string `json:"seat_codes" binding:"required,min=1"`
}

func (h *InventoryHandler) Lock(c *gin.Context) {
	var req LockRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.Error(errors.BadRequest("INVALID_REQUEST", err.Error()))
		return
	}

	err := h.svc.LockSeats(c.Request.Context(), req.ShowtimeID, req.SeatCodes, req.BookingID)
	if err != nil {
		if strings.Contains(err.Error(), "unavailable") {
			h.log.Info("seat_lock_conflict",
				zap.String("booking_id", req.BookingID),
				zap.String("showtime_id", req.ShowtimeID),
				zap.Strings("seat_codes", req.SeatCodes),
				zap.String("error", err.Error()),
			)
		} else {
			h.log.Error("LockSeats system failure",
				zap.Error(err),
				zap.String("booking_id", req.BookingID),
				zap.String("showtime_id", req.ShowtimeID),
				zap.Strings("seat_codes", req.SeatCodes),
			)
		}
		c.Error(errors.Conflict("SEATS_UNAVAILABLE", err.Error()))
		return
	}

	h.log.Info("seat_locked",
		zap.String("booking_id", req.BookingID),
		zap.String("showtime_id", req.ShowtimeID),
		zap.Strings("seat_codes", req.SeatCodes),
		zap.Int("ttl_seconds", 600),
	)

	response.Success(c, gin.H{"message": "Seats locked successfully"})
}

type ReleaseRequest struct {
	ShowtimeID string   `json:"showtime_id" binding:"required,uuid"`
	BookingID  string   `json:"booking_id" binding:"required,uuid"`
	SeatCodes  []string `json:"seat_codes" binding:"required,min=1"`
}

func (h *InventoryHandler) Release(c *gin.Context) {
	var req ReleaseRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.Error(errors.BadRequest("INVALID_REQUEST", err.Error()))
		return
	}

	err := h.svc.ReleaseSeats(c.Request.Context(), req.ShowtimeID, req.SeatCodes, req.BookingID)
	if err != nil {
		c.Error(errors.New(http.StatusInternalServerError, "RELEASE_FAILED", err.Error()))
		return
	}

	response.Success(c, gin.H{"message": "Seats released successfully"})
}

type ConfirmRequest struct {
	ShowtimeID string   `json:"showtime_id" binding:"required,uuid"`
	BookingID  string   `json:"booking_id" binding:"required,uuid"`
	SeatCodes  []string `json:"seat_codes" binding:"required,min=1"`
}

func (h *InventoryHandler) Confirm(c *gin.Context) {
	var req ConfirmRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.Error(errors.BadRequest("INVALID_REQUEST", err.Error()))
		return
	}

	err := h.svc.ConfirmSeats(c.Request.Context(), req.ShowtimeID, req.SeatCodes, req.BookingID)
	if err != nil {
		c.Error(errors.Conflict("CONFIRMATION_FAILED", err.Error()))
		return
	}

	response.Success(c, gin.H{"message": "Seats confirmed successfully"})
}

func (h *InventoryHandler) Summary(c *gin.Context) {
	showtimeID := c.Param("showtime_id")

	summary, err := h.svc.GetSummary(c.Request.Context(), showtimeID)
	if err != nil {
		c.Error(errors.New(http.StatusInternalServerError, "SUMMARY_FAILED", err.Error()))
		return
	}

	response.Success(c, summary)
}
