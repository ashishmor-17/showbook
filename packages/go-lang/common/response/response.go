package response

import (
	"net/http"

	"github.com/ashishmor-17/showbook/packages/go-lang/common/errors"
	"github.com/gin-gonic/gin"
)

// ErrorDetail maps the standard inner JSON format
type ErrorDetail struct {
	Code    string      `json:"code"`
	Message string      `json:"message"`
	Details interface{} `json:"details"`
}

// ErrorResponse is the standardized wrapper response for errors
type ErrorResponse struct {
	Error ErrorDetail `json:"error"`
}

// SuccessResponse wraps successful data payloads under a standard 'data' field
type SuccessResponse struct {
	Data interface{} `json:"data"`
}

// SendError sends a custom formatted error response
func SendError(c *gin.Context, statusCode int, code string, message string, details interface{}) {
	c.JSON(statusCode, ErrorResponse{
		Error: ErrorDetail{
			Code:    code,
			Message: message,
			Details: details,
		},
	})
	c.Abort()
}

// Error renders a standard errors.AppError directly
func Error(c *gin.Context, appErr *errors.AppError) {
	SendError(c, appErr.StatusCode, appErr.Code, appErr.Message, nil)
}

// Success sends an HTTP 200 OK success response
func Success(c *gin.Context, data interface{}) {
	c.JSON(http.StatusOK, SuccessResponse{Data: data})
}

// Created sends an HTTP 201 Created success response
func Created(c *gin.Context, data interface{}) {
	c.JSON(http.StatusCreated, SuccessResponse{Data: data})
}

// NoContent sends an HTTP 204 No Content response
func NoContent(c *gin.Context) {
	c.Status(http.StatusNoContent)
}

// Accepted sends an HTTP 202 Accepted response
func Accepted(c *gin.Context, data interface{}) {
	c.JSON(http.StatusAccepted, SuccessResponse{Data: data})
}
