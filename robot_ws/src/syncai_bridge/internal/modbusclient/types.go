package modbusclient

import "time"

// DoorControlRequest describes a door open/close command.
type DoorControlRequest struct {
	Address    int
	Open       bool
	TimeoutSec time.Duration
}

// DoorControlResponse is the result of a door control operation.
type DoorControlResponse struct {
	Success bool
	Message string
}
