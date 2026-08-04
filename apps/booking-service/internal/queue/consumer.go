package queue

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
	amqp "github.com/rabbitmq/amqp091-go"
	"go.uber.org/zap"

	"github.com/ashishmor-17/showbook/apps/booking-service/internal/service"
)

type PaymentEventPayload struct {
	PaymentTxnID  string  `json:"payment_txn_id"`
	BookingRef    string  `json:"booking_ref"`
	UserID        string  `json:"user_id"`
	Gateway       string  `json:"gateway"`
	Amount        float64 `json:"amount"`
	GatewayTxnID  string  `json:"gateway_txn_id,omitempty"`
	Currency      string  `json:"currency,omitempty"`
	FailureReason string  `json:"failure_reason,omitempty"`
}

type PaymentEventEnvelope struct {
	EventID       string              `json:"event_id"`
	EventType     string              `json:"event_type"`
	EventVersion  int                 `json:"event_version"`
	CorrelationID string              `json:"correlation_id"`
	Payload       PaymentEventPayload `json:"payload"`
}

type PaymentConsumer struct {
	bookingSvc *service.BookingService
	conn       *amqp.Connection
	log        *zap.Logger
}

func NewPaymentConsumer(
	bookingSvc *service.BookingService,
	conn *amqp.Connection,
	log *zap.Logger,
) *PaymentConsumer {
	return &PaymentConsumer{
		bookingSvc: bookingSvc,
		conn:       conn,
		log:        log,
	}
}

func (c *PaymentConsumer) Start(ctx context.Context) {
	ch, err := c.conn.Channel()
	if err != nil {
		c.log.Fatal("Failed to open RabbitMQ channel for consumer", zap.Error(err))
	}
	defer ch.Close()

	// Declare showbook.events exchange (topic, durable)
	err = ch.ExchangeDeclare(
		"showbook.events", // name
		"topic",           // type
		true,              // durable
		false,             // auto-deleted
		false,             // internal
		false,             // no-wait
		nil,               // arguments
	)
	if err != nil {
		c.log.Fatal("Failed to declare exchange in consumer", zap.Error(err))
	}

	// Declare booking_service_payment_queue queue (durable)
	q, err := ch.QueueDeclare(
		"booking_service_payment_queue", // name
		true,                            // durable
		false,                           // delete when unused
		false,                           // exclusive
		false,                           // no-wait
		nil,                             // arguments
	)
	if err != nil {
		c.log.Fatal("Failed to declare queue in consumer", zap.Error(err))
	}

	// Bind to payment.success and payment.failed routing keys
	routingKeys := []string{"payment.success", "payment.failed"}
	for _, key := range routingKeys {
		err = ch.QueueBind(
			q.Name,            // queue name
			key,               // routing key
			"showbook.events", // exchange
			false,
			nil,
		)
		if err != nil {
			c.log.Fatal("Failed to bind queue to exchange in consumer", zap.Error(err), zap.String("routing_key", key))
		}
	}

	// Start consuming
	msgs, err := ch.Consume(
		q.Name, // queue
		"",     // consumer
		false,  // auto-ack (explicit ACK is required!)
		false,  // exclusive
		false,  // no-local
		false,  // no-wait
		nil,    // args
	)
	if err != nil {
		c.log.Fatal("Failed to register a consumer", zap.Error(err))
	}

	c.log.Info("RabbitMQ Payment Events Consumer started", zap.String("queue", q.Name))

	for {
		select {
		case <-ctx.Done():
			c.log.Info("Stopping Payment Events Consumer...")
			return
		case msg, ok := <-msgs:
			if !ok {
				c.log.Warn("Consumer channel closed")
				return
			}

			// Process each message
			c.processMessage(ctx, msg)
		}
	}
}

func (c *PaymentConsumer) processMessage(ctx context.Context, msg amqp.Delivery) {
	var envelope PaymentEventEnvelope
	if err := json.Unmarshal(msg.Body, &envelope); err != nil {
		c.log.Error("Failed to unmarshal payment event JSON", zap.Error(err), zap.ByteString("body", msg.Body))
		// Bad payload format cannot be resolved by retrying, reject it without requeue
		_ = msg.Reject(false)
		return
	}

	c.log.Info("Received payment event",
		zap.String("event_type", envelope.EventType),
		zap.String("booking_ref", envelope.Payload.BookingRef),
		zap.String("txn_id", envelope.Payload.PaymentTxnID),
	)

	// Context with timeout for processing single event
	procCtx, cancel := context.WithTimeout(ctx, 15*time.Second)
	defer cancel()

	var err error
	switch envelope.EventType {
	case "payment.success":
		paymentUUID, parseErr := uuid.Parse(envelope.Payload.PaymentTxnID)
		if parseErr != nil {
			c.log.Error("Invalid payment_txn_id UUID", zap.String("txn_id", envelope.Payload.PaymentTxnID))
			_ = msg.Reject(false)
			return
		}
		err = c.bookingSvc.ConfirmBooking(procCtx, envelope.Payload.BookingRef, paymentUUID, envelope.Payload.Gateway, envelope.Payload.GatewayTxnID)

	case "payment.failed":
		b, _, findErr := c.bookingSvc.GetBookingByRef(procCtx, envelope.Payload.BookingRef)
		if findErr != nil {
			c.log.Error("Failed to find booking for payment failed event", zap.String("booking_ref", envelope.Payload.BookingRef), zap.Error(findErr))
			_ = msg.Reject(false)
			return
		}
		err = c.bookingSvc.CancelBooking(procCtx, b.ID, fmt.Sprintf("Payment failed: %s", envelope.Payload.FailureReason), false)

	default:
		c.log.Warn("Received unknown payment event type", zap.String("event_type", envelope.EventType))
		_ = msg.Ack(false)
		return
	}

	if err != nil {
		c.log.Error("Failed to process payment event", zap.String("event_type", envelope.EventType), zap.Error(err))
		// If the booking is not found, it is a permanent failure (e.g. isolated payment test), reject without requeue
		if errors.Is(err, service.ErrBookingNotFound) {
			_ = msg.Reject(false)
			return
		}
		// Requeue message for retry if it's transient
		_ = msg.Nack(false, true)
		return
	}

	c.log.Info("Successfully processed payment event", zap.String("event_type", envelope.EventType), zap.String("booking_ref", envelope.Payload.BookingRef))
	_ = msg.Ack(false)
}
