package gin

import (
	"time"

	"github.com/ashishmor-17/showbook/packages/go-lang/common/constants"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// RequestLogger logs HTTP requests, injecting latency, status, correlation ID, user-agent, and errors
func RequestLogger(log *zap.Logger) gin.HandlerFunc {
	sugar := log.Sugar()
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		query := c.Request.URL.RawQuery

		c.Next()

		latency := time.Since(start)
		status := c.Writer.Status()
		var corID string
		if val, exists := c.Get(constants.ContextCorrelationIDKey); exists {
			corID, _ = val.(string)
		}

		sugar.Infow("request_processed",
			"status", status,
			"method", c.Request.Method,
			"path", path,
			"query", query,
			"ip", c.ClientIP(),
			"latency_ms", latency.Milliseconds(),
			"correlation_id", corID,
			"errors", len(c.Errors),
			"user_agent", c.Request.UserAgent(),
		)
	}
}
