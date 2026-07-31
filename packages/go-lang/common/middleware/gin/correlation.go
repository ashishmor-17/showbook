package gin

import (
	"github.com/ashishmor-17/showbook/packages/go-lang/common/constants"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// CorrelationID extracts or creates a tracking ID and injects it into context headers
func CorrelationID() gin.HandlerFunc {
	return func(c *gin.Context) {
		corID := c.GetHeader(constants.CorrelationIDHeader)
		if corID == "" {
			corID = uuid.New().String()
		}

		c.Header(constants.CorrelationIDHeader, corID)
		c.Set(constants.ContextCorrelationIDKey, corID)

		c.Next()
	}
}
