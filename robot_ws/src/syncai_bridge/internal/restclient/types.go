package restclient

// MapPayload is the response from GET /api/v1/map.
type MapPayload struct {
	MapMetadata MapMetadata `json:"mapMetadata"`
	Vertexes    []Vertex    `json:"vertexes"`
}

// MapMetadata describes the map grid properties.
type MapMetadata struct {
	MapID      string  `json:"mapId"`
	Resolution float64 `json:"resolution"`
	Width      int     `json:"width"`
	Height     int     `json:"height"`
	Origin     Pose    `json:"origin"`
}

// Pose represents a 2D position with orientation.
type Pose struct {
	X     float64 `json:"x"`
	Y     float64 `json:"y"`
	Theta float64 `json:"theta"`
}

// Vertex is a named position on the map.
type Vertex struct {
	Name string `json:"name"`
	Pose Pose   `json:"pose"`
}

// TaskStepParams holds step parameters. Fields are pointers so absent values omit from JSON.
type TaskStepParams struct {
	X           *float64 `json:"x,omitempty"`
	Y           *float64 `json:"y,omitempty"`
	R           *float64 `json:"r,omitempty"`
	DurationSec *float64 `json:"durationSec,omitempty"`
	Open        *bool    `json:"open,omitempty"`
}

// TaskStep is a single step in a task.
type TaskStep struct {
	ID       string         `json:"id"`
	Name     string         `json:"name"`
	Type     string         `json:"type"`
	Params   TaskStepParams `json:"params"`
	Status   string         `json:"status,omitempty"`
	ErrorMsg string         `json:"error_msg,omitempty"`
}

// TaskPayload contains the steps of a task.
type TaskPayload struct {
	Steps []TaskStep `json:"steps"`
}

// TaskCreateRequest is the body for POST /api/v1/tasks/.
type TaskCreateRequest struct {
	Action    string      `json:"action"`
	ID        string      `json:"id"`
	Timestamp float64     `json:"timestamp"`
	Payload   TaskPayload `json:"payload"`
}

// TaskCreateResponse is the response from POST /api/v1/tasks/.
type TaskCreateResponse struct {
	ID      string `json:"id"`
	Status  string `json:"status"`
	Message string `json:"message"`
}

// Task is the full task object returned by GET endpoints.
type Task struct {
	Action           string      `json:"action"`
	ID               string      `json:"id"`
	Timestamp        float64     `json:"timestamp"`
	Payload          TaskPayload `json:"payload"`
	Status           string      `json:"status"`
	CurrentStepIndex int         `json:"current_step_index"`
	ErrorMsg         string      `json:"error_msg"`
	WorkflowID       string      `json:"workflow_id"`
	CompletedAt      float64     `json:"completed_at"`
}
