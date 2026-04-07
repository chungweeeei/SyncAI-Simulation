package restclient

import (
	"context"
	"encoding/json"
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

// GetMap calls GET /api/v1/map and returns the map payload.
func (c *Client) GetMap(ctx context.Context) (*MapPayload, error) {
	url := c.baseURL + "/api/v1/map"

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("build request: %w", err)
	}

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("GET %s: %w", url, err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, &HTTPError{
			StatusCode: resp.StatusCode,
			Detail:     string(body),
		}
	}

	var payload MapPayload
	if err := json.Unmarshal(body, &payload); err != nil {
		return nil, fmt.Errorf("unmarshal map response: %w", err)
	}
	return &payload, nil
}
