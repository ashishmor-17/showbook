package models

import (
	"time"

	"github.com/google/uuid"
)

type SeatStatus string

const (
	SeatAvailable SeatStatus = "AVAILABLE"
	SeatLocked    SeatStatus = "LOCKED"
	SeatBooked    SeatStatus = "BOOKED"
	SeatBlocked   SeatStatus = "BLOCKED"
)

type SeatInventory struct {
	ID                uuid.UUID  `json:"id" db:"id"`
	ShowtimeID        uuid.UUID  `json:"showtime_id" db:"showtime_id"`
	SeatLayoutID      uuid.UUID  `json:"seat_layout_id" db:"seat_layout_id"`
	SeatCode          string     `json:"seat_code" db:"seat_code"`
	SeatTypeID        uuid.UUID  `json:"seat_type_id" db:"seat_type_id"`
	Status            SeatStatus `json:"status" db:"status"`
	LockedByBookingID *uuid.UUID `json:"locked_by_booking_id,omitempty" db:"locked_by_booking_id"`
	LockedUntil       *time.Time `json:"locked_until,omitempty" db:"locked_until"`
	BookedByBookingID *uuid.UUID `json:"booked_by_booking_id,omitempty" db:"booked_by_booking_id"`
	Version           int        `json:"version" db:"version"`
	UpdatedAt         time.Time  `json:"updated_at" db:"updated_at"`
}
