package main

import (
	"context"
	"os/signal"
	"syscall"
	"time"

	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/booking-service/db/migrations"
	"github.com/ashishmor-17/showbook/apps/booking-service/internal/handlers"
	"github.com/ashishmor-17/showbook/apps/booking-service/internal/repository"
	"github.com/ashishmor-17/showbook/apps/booking-service/internal/server"
	"github.com/ashishmor-17/showbook/apps/booking-service/internal/service"
	"github.com/ashishmor-17/showbook/apps/booking-service/internal/utils"
	"github.com/ashishmor-17/showbook/apps/booking-service/internal/worker"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/clients"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/config"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/database"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/logger"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/queue"
)

func main() {
	appCtx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	logLevel := config.GetEnv("LOG_LEVEL", "INFO")
	log, err := logger.New("booking-service", logLevel)
	if err != nil {
		panic("Failed to initialize logger: " + err.Error())
	}
	defer func() { _ = log.Sync() }()

	log.Info("Starting Booking Service...")

	dbURL := config.GetEnv("DATABASE_URL", "postgresql://showbook:showbook@localhost:5432/showbook_booking")
	pgPool, err := database.NewPostgres(dbURL)
	if err != nil {
		log.Fatal("Failed to connect to Postgres", zap.Error(err))
	}
	defer pgPool.Close()

	rabbitmqURL := config.GetEnv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
	rabbitmqConn, rabbitmqCh, err := queue.NewRabbitMQ(rabbitmqURL)
	if err != nil {
		log.Fatal("Failed to connect to RabbitMQ", zap.Error(err))
	}
	defer rabbitmqConn.Close()
	defer rabbitmqCh.Close()

	migrationCtx, migrationCancel := context.WithTimeout(appCtx, 15*time.Second)
	defer migrationCancel()
	if err := migrations.Run(migrationCtx, pgPool, log); err != nil {
		log.Fatal("Failed to run database migrations", zap.Error(err))
	}

	venueServiceURL := config.GetEnv("VENUE_SERVICE_URL", "http://localhost:8001")
	inventoryServiceURL := config.GetEnv("INVENTORY_SERVICE_URL", "http://localhost:8003")

	httpClient := clients.NewHTTPClient(5 * time.Second)
	bookingRepo := repository.NewBookingRepository(pgPool)
	timeProvider := utils.RealTimeProvider{}
	bookingSvc := service.NewBookingService(bookingRepo, httpClient, venueServiceURL, inventoryServiceURL, timeProvider, log)
	bookingHandler := handlers.NewBookingHandler(bookingSvc, log)

	srv := server.New(log, pgPool, bookingHandler)

	// Outbox worker
	outboxWorker := worker.NewOutboxWorker(bookingRepo, rabbitmqCh, httpClient, inventoryServiceURL, log)
	go outboxWorker.Start(appCtx)

	// Expiry worker
	expiryWorker := worker.NewExpiryWorker(bookingRepo, log)
	go expiryWorker.Start(appCtx)

	port := config.GetEnv("PORT", "8006")
	srv.Start(port)

	<-appCtx.Done()

	log.Info("Shutting down Booking Service gracefully...")
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer shutdownCancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Error("Server forced to shutdown", zap.Error(err))
	}

	log.Info("Server exiting successfully.")
}
