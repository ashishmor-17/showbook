CREATE TABLE IF NOT EXISTS seat_inventory (
    id UUID PRIMARY KEY,

    showtime_id UUID NOT NULL,
    seat_layout_id UUID NOT NULL,

    seat_code TEXT NOT NULL,
    seat_type_id UUID NOT NULL,

    status TEXT NOT NULL DEFAULT 'AVAILABLE'
        CHECK (status IN ('AVAILABLE', 'LOCKED', 'BOOKED', 'BLOCKED')),

    locked_by_booking_id UUID NULL,
    locked_until TIMESTAMPTZ NULL,

    booked_by_booking_id UUID NULL,

    version INTEGER NOT NULL DEFAULT 1,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_showtime_seat
        UNIQUE(showtime_id, seat_layout_id)
);


CREATE INDEX IF NOT EXISTS idx_inventory_showtime
ON seat_inventory(showtime_id, status);


CREATE INDEX IF NOT EXISTS idx_inventory_locked_until
ON seat_inventory(locked_until)
WHERE status = 'LOCKED';