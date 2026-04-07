package restclient

import (
	"bytes"
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

// CreateTask calls POST /api/v1/tasks/.
func (c *Client) CreateTask(ctx context.Context, req *TaskCreateRequest) (*TaskCreateResponse, error) {
	url := c.baseURL + "/api/v1/tasks/"

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("build request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.http.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("POST %s: %w", url, err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return nil, &HTTPError{StatusCode: resp.StatusCode, Detail: string(respBody)}
	}

	var result TaskCreateResponse
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("unmarshal create task response: %w", err)
	}
	return &result, nil
}

// ListTasks calls GET /api/v1/tasks/.
func (c *Client) ListTasks(ctx context.Context) ([]Task, error) {
	url := c.baseURL + "/api/v1/tasks/"

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
		return nil, &HTTPError{StatusCode: resp.StatusCode, Detail: string(body)}
	}

	var tasks []Task
	if err := json.Unmarshal(body, &tasks); err != nil {
		return nil, fmt.Errorf("unmarshal tasks response: %w", err)
	}
	return tasks, nil
}

// GetTask calls GET /api/v1/tasks/{taskID}.
func (c *Client) GetTask(ctx context.Context, taskID string) (*Task, error) {
	url := c.baseURL + "/api/v1/tasks/" + taskID

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
		return nil, &HTTPError{StatusCode: resp.StatusCode, Detail: string(body)}
	}

	var task Task
	if err := json.Unmarshal(body, &task); err != nil {
		return nil, fmt.Errorf("unmarshal task response: %w", err)
	}
	return &task, nil
}
