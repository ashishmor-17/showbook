package redislock

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

var (
	// Multi-key lock check and set script with booking_id idempotency
	lockLua = redis.NewScript(`
		for i, key in ipairs(KEYS) do
			local existing = redis.call('GET', key)
			if existing ~= false then
				if existing ~= ARGV[1] then
					return {0, key, existing}
				end
			end
		end
		for i, key in ipairs(KEYS) do
			redis.call('SET', key, ARGV[1], 'NX', 'EX', tonumber(ARGV[2]))
		end
		return {1, ""}
	`)

	// Multi-key release script (only deletes if value matches booking_id)
	releaseLua = redis.NewScript(`
		for i, key in ipairs(KEYS) do
			local val = redis.call('GET', key)
			if val == ARGV[1] then
				redis.call('DEL', key)
			end
		end
		return 1
	`)
)

type LockClient struct {
	rdb *redis.Client
}

func NewLockClient(rdb *redis.Client) *LockClient {
	return &LockClient{rdb: rdb}
}

func LockKey(showtimeID, seatCode string) string {
	return fmt.Sprintf("inventory:lock:%s:%s", showtimeID, seatCode)
}

func SummaryKey(showtimeID string) string {
	return fmt.Sprintf("inventory:summary:%s", showtimeID)
}

// AcquireLocks attempts to atomically lock multiple keys in Redis
func (c *LockClient) AcquireLocks(ctx context.Context, showtimeID string, seatCodes []string, bookingID string, ttl time.Duration) (bool, string, error) {
	keys := make([]string, len(seatCodes))
	for i, code := range seatCodes {
		keys[i] = LockKey(showtimeID, code)
	}

	ttlSeconds := int64(ttl.Seconds())
	res, err := lockLua.Run(ctx, c.rdb, keys, bookingID, ttlSeconds).Result()
	if err != nil {
		return false, "", err
	}

	resSlice, ok := res.([]interface{})
	if !ok || len(resSlice) < 1 {
		return false, "", fmt.Errorf("unexpected Redis script result format")
	}

	success := resSlice[0].(int64) == 1
	if !success {
		return false, resSlice[1].(string), nil
	}

	return true, "", nil
}

// ReleaseLocks releases locks in Redis if they belong to the given bookingID
func (c *LockClient) ReleaseLocks(ctx context.Context, showtimeID string, seatCodes []string, bookingID string) error {
	keys := make([]string, len(seatCodes))
	for i, code := range seatCodes {
		keys[i] = LockKey(showtimeID, code)
	}

	_, err := releaseLua.Run(ctx, c.rdb, keys, bookingID).Result()
	return err
}

func (c *LockClient) InvalidateSummary(ctx context.Context, showtimeID string) error {
	return c.rdb.Del(ctx, SummaryKey(showtimeID)).Err()
}

func (c *LockClient) GetSummary(ctx context.Context, showtimeID string) (string, error) {
	return c.rdb.Get(ctx, SummaryKey(showtimeID)).Result()
}

func (c *LockClient) SetSummary(ctx context.Context, showtimeID string, val string, ttl time.Duration) error {
	return c.rdb.Set(ctx, SummaryKey(showtimeID), val, ttl).Err()
}
