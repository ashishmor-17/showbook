package errors

import "fmt"

// AppError represents a structured, HTTP-agnostic domain error
type AppError struct {
	StatusCode int    `json:"-"`
	Code       string `json:"code"`
	Message    string `json:"message"`
}

func (e *AppError) Error() string {
	return fmt.Sprintf("[%s] %s", e.Code, e.Message)
}

func New(statusCode int, code string, message string) *AppError {
	return &AppError{
		StatusCode: statusCode,
		Code:       code,
		Message:    message,
	}
}

// Helper constructors
func BadRequest(code, message string) *AppError {
	return New(400, code, message)
}

func Unauthorized(code, message string) *AppError {
	return New(401, code, message)
}

func NotFound(code, message string) *AppError {
	return New(404, code, message)
}

func Conflict(code, message string) *AppError {
	return New(409, code, message)
}
