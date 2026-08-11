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
	r.GET("/live", s.handleLive())
	r.GET("/ready", s.handleReady(pgPool))

	api := r.Group("/api/v1")
	{
		api.POST("/bookings/initiate", bookingHandler.Initiate)
		api.GET("/bookings/:booking_ref", bookingHandler.Get)
		api.GET("/bookings", bookingHandler.List)
		api.POST("/bookings/:booking_ref/cancel", bookingHandler.Cancel)
	}
}
