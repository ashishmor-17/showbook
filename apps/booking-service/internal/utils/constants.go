package utils

const (
	StatusInitiated      = "INITIATED"
	StatusPaymentPending = "PAYMENT_PENDING"
	StatusConfirmed      = "CONFIRMED"
	StatusCancelled      = "CANCELLED"
	StatusExpired        = "EXPIRED"
	StatusRefunded       = "REFUNDED"

	ShowtimeStatusOpen = "OPEN"

	OutboxStatusPending    = "PENDING"
	OutboxStatusProcessing = "PROCESSING"
	OutboxStatusPublished  = "PUBLISHED"
	OutboxStatusFailed     = "FAILED"
	OutboxStatusDead       = "DEAD"

	EventBookingInitiated         = "booking.initiated"
	EventBookingFailed            = "booking.failed"
	EventBookingExpired           = "booking.expired"
	EventInventoryReleaseRequested = "inventory.release.requested"
	EventBookingConfirmed         = "booking.confirmed"
	EventBookingCancelled         = "booking.cancelled"
)
