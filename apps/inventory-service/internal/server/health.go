package server

import (
	"context"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/redis/go-redis/v9"
)

func (s *Server) handleHealth(pgPool *pgxpool.Pool, redisClient *redis.Client) gin.HandlerFunc {
	return s.handleReady(pgPool, redisClient)
}

func (s *Server) handleLive() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "UP",
			"service": "inventory-service",
		})
	}
}

func (s *Server) handleReady(pgPool *pgxpool.Pool, redisClient *redis.Client) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx, cancel := context.WithTimeout(c.Request.Context(), 2*time.Second)
		defer cancel()

		dbErr := pgPool.Ping(ctx)
		redisErr := redisClient.Ping(ctx).Err()

		if dbErr != nil || redisErr != nil {
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"status":    "DOWN",
				"service":   "inventory-service",
				"postgres":  dbErr == nil,
				"redis":     redisErr == nil,
			})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"status":   "UP",
			"service":  "inventory-service",
			"postgres": "UP",
			"redis":    "UP",
		})
	}
}
