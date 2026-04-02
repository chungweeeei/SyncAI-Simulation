package dds

import "math"

// RobotState is the Go domain model for a robot's state.
type RobotState struct {
	TimestampSec  int32   `json:"timestamp_sec"`
	TimestampNsec uint32  `json:"timestamp_nsec"`
	FrameID       string  `json:"frame_id"`
	RobotID       string  `json:"robot_id"`
	RobotName     string  `json:"robot_name"`
	Model         string  `json:"model"`
	Map           string  `json:"map"`
	PoseX         float64 `json:"pose_x"`
	PoseY         float64 `json:"pose_y"`
	PoseZ         float64 `json:"pose_z"`
	OrientX       float64 `json:"orient_x"`
	OrientY       float64 `json:"orient_y"`
	OrientZ       float64 `json:"orient_z"`
	OrientW       float64 `json:"orient_w"`
	LinearX       float64 `json:"linear_x"`
	LinearY       float64 `json:"linear_y"`
	LinearZ       float64 `json:"linear_z"`
	AngularX      float64 `json:"angular_x"`
	AngularY      float64 `json:"angular_y"`
	AngularZ      float64 `json:"angular_z"`
	BatteryPct    float32 `json:"battery_percentage"`
	BatteryV      float32 `json:"battery_voltage"`
}

// Timestamp returns the combined timestamp as float64 seconds.
func (r *RobotState) Timestamp() float64 {
	return float64(r.TimestampSec) + float64(r.TimestampNsec)*1e-9
}

// Yaw computes yaw from the quaternion orientation.
func (r *RobotState) Yaw() float64 {
	sinyCosp := 2.0 * (r.OrientW*r.OrientZ + r.OrientX*r.OrientY)
	cosyCosp := 1.0 - 2.0*(r.OrientY*r.OrientY+r.OrientZ*r.OrientZ)
	return math.Atan2(sinyCosp, cosyCosp)
}
