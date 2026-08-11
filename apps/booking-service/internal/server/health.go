// apps/booking-service/internal/server/health.go
package server

import (
	"context"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"
)

func (s *Server) handleHealth(pgPool *pgxpool.Pool) gin.HandlerFunc {
	return s.handleReady(pgPool)
}

func (s *Server) handleLive() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "UP",
			"service": "booking-service",
		})
	}
}

func (s *Server) handleReady(pgPool *pgxpool.Pool) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx, cancel := context.WithTimeout(c.Request.Context(), 2*time.Second)
		defer cancel()

		dbErr := pgPool.Ping(ctx)

		if dbErr != nil {
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"status":   "DOWN",
				"service":  "booking-service",
				"postgres": "DOWN",
			})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"status":   "UP",
			"service":  "booking-service",
			"postgres": "UP",
		})
	}
}
