package server

import (
	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/redis/go-redis/v9"

	"github.com/ashishmor-17/showbook/apps/inventory-service/internal/handlers"
)

func (s *Server) setupRoutes(
	r *gin.Engine,
	pgPool *pgxpool.Pool,
	redisClient *redis.Client,
	inventoryHandler *handlers.InventoryHandler,
) {
	r.GET("/health", s.handleHealth(pgPool, redisClient))

	api := r.Group("/api/v1")
	{
		api.POST("/inventory/lock", inventoryHandler.Lock)
		api.POST("/inventory/release", inventoryHandler.Release)
		api.POST("/inventory/confirm", inventoryHandler.Confirm)
		api.GET("/inventory/showtime/:showtime_id/summary", inventoryHandler.Summary)
	}
}
