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

// Client calls the robot's local REST API (syncai_robot_api).
type Client struct {
	baseURL string
	http    *http.Client
	logger  *slog.Logger
}

// New creates a REST client targeting the given base URL (e.g. "http://localhost:3000").
func New(baseURL string, logger *slog.Logger) *Client {
	return &Client{
		baseURL: baseURL,
		http: &http.Client{
			Timeout: 10 * time.Second,
		},
		logger: logger,
	}
}

// SendRequest makes a generic HTTP request and returns the raw response body.
func (c *Client) SendRequest(ctx context.Context, method, path, body string) ([]byte, error) {
	url := c.baseURL + path

	var reqBody io.Reader
	if body != "" {
		reqBody = bytes.NewReader([]byte(body))
	}

	req, err := http.NewRequestWithContext(ctx, method, url, reqBody)
	if err != nil {
		return nil, fmt.Errorf("build request: %w", err)
	}
	if body != "" {
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

