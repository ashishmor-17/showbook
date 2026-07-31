package gin

import (
	"net/http"

	"github.com/ashishmor-17/showbook/packages/go-lang/common/errors"
	"github.com/ashishmor-17/showbook/packages/go-lang/common/response"
	"github.com/gin-gonic/gin"
)

// ErrorHandler processes context errors, formatting them using response.Error or response.SendError
func ErrorHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Next()

		if len(c.Errors) > 0 {
			err := c.Errors.Last().Err
			if appErr, ok := err.(*errors.AppError); ok {
				response.Error(c, appErr)
				return
			}

			// Fallback for unhandled generic Go errors
			response.SendError(
				c,
				http.StatusInternalServerError,
				"INTERNAL_SERVER_ERROR",
				err.Error(),
				nil,
			)
		}
	}
}
