package gin

import (
	"net/http"

	"github.com/ashishmor-17/showbook/packages/go-lang/common/constants"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/response"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// Recovery catches panics, logs stack traces via the injected logger, and writes a standard error response
func Recovery(log *zap.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if err := recover(); err != nil {
				var corID string
				if val, exists := c.Get(constants.ContextCorrelationIDKey); exists {
					corID, _ = val.(string)
				}

				log.Error("panic_recovered",
					zap.Any("error", err),
					zap.String("correlation_id", corID),
				)

				response.SendError(
					c,
					http.StatusInternalServerError,
					"INTERNAL_SERVER_ERROR",
					"An unexpected error occurred",
					nil,
				)
			}
		}()
		c.Next()
	}
}
