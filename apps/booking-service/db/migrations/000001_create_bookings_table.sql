-- apps/booking-service/db/migrations/000001_create_bookings_table.sql
CREATE TABLE IF NOT EXISTS bookings (
    id UUID PRIMARY KEY,
    booking_ref VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL,
    showtime_id UUID NOT NULL,
    status VARCHAR(50) DEFAULT 'INITIATED' CHECK (status IN ('INITIATED', 'PAYMENT_PENDING', 'CONFIRMED', 'CANCELLED', 'EXPIRED', 'REFUNDED')),
    total_amount_paise BIGINT NOT NULL,
    convenience_fee_paise BIGINT DEFAULT 0,
    discount_amount_paise BIGINT DEFAULT 0,
    final_amount_paise BIGINT NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    expires_at TIMESTAMPTZ NOT NULL,
    idempotency_key VARCHAR(255) NULL,
    request_hash VARCHAR(64) NULL,
    lock_token VARCHAR(255) NULL,
    
    payment_id UUID NULL,
    payment_provider VARCHAR(50) NULL,
    payment_provider_order_id VARCHAR(255) NULL,
    payment_provider_payment_id VARCHAR(255) NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_idempotency ON bookings(idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_bookings_request_hash ON bookings(request_hash) WHERE request_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS booking_seats (
    id UUID PRIMARY KEY,
    booking_id UUID REFERENCES bookings(id) ON DELETE CASCADE,
    seat_code VARCHAR(50) NOT NULL,
    seat_type_name VARCHAR(100) NOT NULL,
    unit_price_paise BIGINT NOT NULL,
    convenience_fee_paise BIGINT NOT NULL,
    UNIQUE(booking_id, seat_code)
);

CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY,
    booking_id UUID REFERENCES bookings(id),
    seat_code VARCHAR(50) NOT NULL,
    barcode VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'VALID' CHECK (status IN ('VALID', 'USED', 'CANCELLED')),
    issued_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS outbox (
    id UUID PRIMARY KEY,
    event_id UUID UNIQUE NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_version INTEGER NOT NULL DEFAULT 1,
    aggregate_type VARCHAR(255) NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'PUBLISHED', 'FAILED', 'DEAD')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    next_attempt_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_showtime ON bookings(showtime_id) WHERE status = 'CONFIRMED';
CREATE INDEX idx_bookings_expires ON bookings(expires_at) WHERE status IN ('INITIATED', 'PAYMENT_PENDING');
CREATE INDEX idx_outbox_pending ON outbox(status, created_at) WHERE status = 'PENDING';
