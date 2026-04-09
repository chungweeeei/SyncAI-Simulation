package restclient

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"time"
)

// Client makes HTTP requests to external REST APIs.
type Client struct {
	http   *http.Client
	logger *slog.Logger
}

// New creates a REST client.
func New(logger *slog.Logger) *Client {
	return &Client{
		http: &http.Client{
			Timeout: 10 * time.Second,
		},
		logger: logger,
	}
}

// SendRequest makes a generic HTTP request to the given full URL and returns the raw response body.
func (c *Client) SendRequest(ctx context.Context, method, url, body string, headers map[string]string) ([]byte, error) {
	var reqBody io.Reader
	if body != "" {
		reqBody = bytes.NewReader([]byte(body))
	}

	req, err := http.NewRequestWithContext(ctx, method, url, reqBody)
	if err != nil {
		return nil, fmt.Errorf("build request: %w", err)
	}

	// Apply custom headers.
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	// Default Content-Type to application/json if body is present and not already set.
	if body != "" && req.Header.Get("Content-Type") == "" {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("%s %s: %w", method, url, err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, &HTTPError{StatusCode: resp.StatusCode, Detail: string(respBody)}
	}

	return respBody, nil
}
