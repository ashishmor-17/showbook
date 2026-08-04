// apps/booking-service/internal/server/routes.go
package server

import (
	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/ashishmor-17/showbook/apps/booking-service/internal/handlers"
)

func (s *Server) setupRoutes(
	r *gin.Engine,
	pgPool *pgxpool.Pool,
	bookingHandler *handlers.BookingHandler,
) {
	r.GET("/health", s.handleHealth(pgPool))

	api := r.Group("/api/v1")
	{
		api.POST("/bookings/initiate", bookingHandler.Initiate)
		api.GET("/bookings/:booking_ref", bookingHandler.Get)
		api.GET("/bookings", bookingHandler.List)
		api.POST("/bookings/:booking_id/cancel", bookingHandler.Cancel)
	}
}
