package worker

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"
	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/booking-service/internal/repository"
	"github.com/ashishmor-17/showbook/apps/booking-service/internal/utils"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/clients"
)

type OutboxWorker struct {
	repo                *repository.BookingRepository
	amqpCh              *amqp.Channel
	httpClient          *clients.HTTPClient
	inventoryServiceURL string
	log                 *zap.Logger
}

func NewOutboxWorker(
	repo *repository.BookingRepository,
	amqpCh *amqp.Channel,
	httpClient *clients.HTTPClient,
	inventoryServiceURL string,
	log *zap.Logger,
) *OutboxWorker {
	return &OutboxWorker{
		repo:                repo,
		amqpCh:              amqpCh,
		httpClient:          httpClient,
		inventoryServiceURL: inventoryServiceURL,
		log:                 log,
	}
}

func (w *OutboxWorker) Start(ctx context.Context) {
	if err := w.amqpCh.Confirm(false); err != nil {
		w.log.Fatal("Failed to set RabbitMQ channel to confirm mode", zap.Error(err))
	}

	err := w.amqpCh.ExchangeDeclare(
		"showbook.events", "topic", true, false, false, false, nil,
	)
	if err != nil {
		w.log.Fatal("Failed to declare RabbitMQ exchange", zap.Error(err))
	}

	confirms := w.amqpCh.NotifyPublish(make(chan amqp.Confirmation, 100))

	w.log.Info("Transactional Outbox Worker running (Confirm and schedule mode).")
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			w.processPendingEvents(ctx, confirms)
		}
	}
}

func (w *OutboxWorker) processPendingEvents(ctx context.Context, confirms <-chan amqp.Confirmation) {
	events, err := w.repo.FetchAndLockOutbox(ctx, 20)
	if err != nil {
		w.log.Error("Failed to fetch pending outbox events", zap.Error(err))
		return
	}

	for _, e := range events {
		if e.EventType == utils.EventInventoryReleaseRequested {
			err = w.executeInventoryRelease(ctx, e.Payload)
			if err != nil {
				w.log.Error("Failed to execute async inventory release, scheduling retry", zap.Error(err))
				_ = w.repo.UpdateOutboxStatus(ctx, e, "FAILED")
			} else {
				_ = w.repo.UpdateOutboxStatus(ctx, e, "PUBLISHED")
			}
			continue
		}

		payloadBytes, err := json.Marshal(e.Payload)
		if err != nil {
			w.log.Error("Failed serializing event payload", zap.Error(err))
			_ = w.repo.UpdateOutboxStatus(ctx, e, "FAILED")
			continue
		}

		err = w.amqpCh.PublishWithContext(
			ctx,
			"showbook.events",
			e.EventType,
			false,
			false,
			amqp.Publishing{
				MessageId:    e.EventID.String(),
				ContentType:  "application/json",
				Timestamp:    time.Now(),
				Body:         payloadBytes,
				DeliveryMode: amqp.Persistent,
			},
		)

		if err != nil {
			w.log.Error("Failed publishing to AMQP", zap.Error(err))
			_ = w.repo.UpdateOutboxStatus(ctx, e, "FAILED")
			continue
		}

		select {
		case confirm := <-confirms:
			if confirm.Ack {
				_ = w.repo.UpdateOutboxStatus(ctx, e, "PUBLISHED")
			} else {
				w.log.Warn("AMQP Publish Nacked", zap.String("event_id", e.EventID.String()))
				_ = w.repo.UpdateOutboxStatus(ctx, e, "FAILED")
			}
		case <-time.After(3 * time.Second):
			w.log.Warn("AMQP Publish Confirm timeout", zap.String("event_id", e.EventID.String()))
			_ = w.repo.UpdateOutboxStatus(ctx, e, "FAILED")
		}
	}
}

func (w *OutboxWorker) executeInventoryRelease(ctx context.Context, payload any) error {
	payloadMap, ok := payload.(map[string]any)
	if !ok {
		return fmt.Errorf("invalid payload format for inventory release")
	}

	if seatCodes, exists := payloadMap["seat_codes"]; exists {
		if codes, ok := seatCodes.([]any); ok && len(codes) == 0 {
			w.log.Info("Skipping inventory release: empty seat_codes array")
			return nil
		}
		if codes, ok := seatCodes.([]string); ok && len(codes) == 0 {
			w.log.Info("Skipping inventory release: empty seat_codes string array")
			return nil
		}
	}

	bodyBytes, err := json.Marshal(payloadMap)
	if err != nil {
		return err
	}

	releaseCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()

	url := fmt.Sprintf("%s/api/v1/inventory/release", w.inventoryServiceURL)
	req, err := http.NewRequestWithContext(releaseCtx, "POST", url, bytes.NewBuffer(bodyBytes))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := w.httpClient.Do(releaseCtx, req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("received non-200 code from inventory release: %d, response: %s", resp.StatusCode, string(respBody))
	}

	return nil
}
