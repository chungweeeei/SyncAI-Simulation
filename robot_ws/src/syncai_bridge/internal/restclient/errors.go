package restclient

import "fmt"

// HTTPError represents a non-2xx HTTP response from the robot API.
type HTTPError struct {
	StatusCode int
	Detail     string
}

func (e *HTTPError) Error() string {
	return fmt.Sprintf("robot API returned %d: %s", e.StatusCode, e.Detail)
}
