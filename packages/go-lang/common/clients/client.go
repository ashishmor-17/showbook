package clients

import (
	"context"
	"net/http"
	"time"

	"github.com/ashishmor-17/showbook/packages/go-lang/common/constants"
)

type HTTPClient struct {
	client *http.Client
}

func NewHTTPClient(timeout time.Duration) *HTTPClient {
	return &HTTPClient{
		client: &http.Client{
			Timeout: timeout,
		},
	}
}

// Do executes an HTTP request, automatically extracting and injecting the Correlation ID
func (c *HTTPClient) Do(ctx context.Context, req *http.Request) (*http.Response, error) {
	if corID, ok := ctx.Value(constants.ContextCorrelationIDKey).(string); ok && corID != "" {
		req.Header.Set(constants.CorrelationIDHeader, corID)
	}
	return c.client.Do(req.WithContext(ctx))
}
