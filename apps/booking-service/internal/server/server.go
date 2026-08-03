// apps/booking-service/internal/server/server.go
package server

import (
	"context"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"
	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/booking-service/internal/handlers"
	ginMiddleware "github.com/ashishmor-17/showbook/packages/go-lang/common/middleware/gin"
)

type Server struct {
	httpServer *http.Server
	log        *zap.Logger
}

func New(
	log *zap.Logger,
	pgPool *pgxpool.Pool,
	bookingHandler *handlers.BookingHandler,
) *Server {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()

	r.Use(ginMiddleware.CorrelationID())
	r.Use(ginMiddleware.RequestLogger(log))
	r.Use(ginMiddleware.Recovery(log))
	r.Use(ginMiddleware.ErrorHandler())

	s := &Server{log: log}
	s.setupRoutes(r, pgPool, bookingHandler)

	s.httpServer = &http.Server{Handler: r}
	return s
}

func (s *Server) Start(port string) {
	s.httpServer.Addr = ":" + port
	go func() {
		s.log.Info("Booking Service listening", zap.String("port", port))
		if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			s.log.Fatal("Failed to listen and serve", zap.Error(err))
		}
	}()
}

func (s *Server) Shutdown(ctx context.Context) error {
	return s.httpServer.Shutdown(ctx)
}
