package main

import (
	"context"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/inventory-service/db/migrations"
	"github.com/ashishmor-17/showbook/apps/inventory-service/internal/handlers"
	"github.com/ashishmor-17/showbook/apps/inventory-service/internal/redislock"
	"github.com/ashishmor-17/showbook/apps/inventory-service/internal/repository"
	"github.com/ashishmor-17/showbook/apps/inventory-service/internal/server"
	"github.com/ashishmor-17/showbook/apps/inventory-service/internal/service"
	"github.com/ashishmor-17/showbook/apps/inventory-service/internal/worker"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/config"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/database"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/logger"
)

func main() {
	// Setup unified context for application lifecycle
	appCtx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	// Initialize Zap Logger
	logLevel := config.GetEnv("LOG_LEVEL", "INFO")
	log, err := logger.New("inventory-service", logLevel)
	if err != nil {
		panic("Failed to initialize logger: " + err.Error())
	}
	defer func() { _ = log.Sync() }()

	log.Info("Starting Inventory Service...")

	// Initialize Postgres Pool
	dbURL := config.GetEnv("DATABASE_URL", "postgresql://showbook:showbook@localhost:5432/showbook_inventory")
	pgPool, err := database.NewPostgres(dbURL)
	if err != nil {
		log.Fatal("Failed to connect to Postgres", zap.Error(err))
	}
	defer pgPool.Close()

	// Initialize Redis Client
	redisHost := config.GetEnv("REDIS_HOST", "localhost")
	redisPortStr := config.GetEnv("REDIS_PORT", "6379")
	redisPort, err := strconv.Atoi(redisPortStr)
	if err != nil {
		log.Fatal("Invalid REDIS_PORT configuration", zap.Error(err))
	}
	redisPassword := config.GetEnv("REDIS_PASSWORD", "redis_password")

	redisClientObj, err := database.NewRedis(redisHost+":"+strconv.Itoa(redisPort), redisPassword, 0)
	if err != nil {
		log.Fatal("Failed to connect to Redis", zap.Error(err))
	}
	defer func() { _ = redisClientObj.Close() }()

	// Run Database Migrations
	migrationCtx, migrationCancel := context.WithTimeout(appCtx, 15*time.Second)
	defer migrationCancel()
	if err := migrations.Run(migrationCtx, pgPool, log); err != nil {
		log.Fatal("Failed to run database migrations", zap.Error(err))
	}

	// Setup Layered Dependencies
	seatRepo := repository.NewSeatRepository(pgPool)
	lockClient := redislock.NewLockClient(redisClientObj)
	svc := service.NewInventoryService(seatRepo, lockClient, log)
	inventoryHandler := handlers.NewInventoryHandler(svc, log)

	// Initialize Server Abstraction
	srv := server.New(log, pgPool, redisClientObj, inventoryHandler)

	// Start Background Lock Expiry Worker
	worker.StartLockExpiryWorker(appCtx, seatRepo, lockClient, log)

	// Start Server
	port := config.GetEnv("PORT", "8003")
	srv.Start(port)

	// Wait for shutdown signals mapped through signal.NotifyContext
	<-appCtx.Done()

	log.Info("Shutting down Inventory Service gracefully.")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer shutdownCancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Error("Server forced to shutdown", zap.Error(err))
	}

	log.Info("Server exiting successfully.")
}
