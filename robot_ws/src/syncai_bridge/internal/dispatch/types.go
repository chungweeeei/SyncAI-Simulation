package dispatch

// Request is a protocol-agnostic dispatch request.
type Request struct {
	Protocol string         `json:"protocol"` // e.g. "dds"
	Target   string         `json:"target"`   // e.g. "robot01"
	Action   string         `json:"action"`   // e.g. "cmd_vel"
	Payload  map[string]any `json:"payload"`  // action-specific parameters
}

// Response is the result of dispatching a request.
type Response struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}
