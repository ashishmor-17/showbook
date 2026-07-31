package queue

import (
	"fmt"

	amqp "github.com/rabbitmq/amqp091-go"
)

// NewRabbitMQ establishes a connection and channel for AMQP messaging
func NewRabbitMQ(connStr string) (*amqp.Connection, *amqp.Channel, error) {
	conn, err := amqp.Dial(connStr)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to connect to RabbitMQ: %w", err)
	}

	ch, err := conn.Channel()
	if err != nil {
		_ = conn.Close()
		return nil, nil, fmt.Errorf("failed to open a channel: %w", err)
	}

	return conn, ch, nil
}
