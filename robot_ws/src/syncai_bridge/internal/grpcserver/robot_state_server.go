package grpcserver

import (
	"log/slog"
	"sync/atomic"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	"github.com/nicosyncai/syncai-bridge/internal/dds"
	pb "github.com/nicosyncai/syncai-bridge/internal/grpcserver/pb"
)

// RobotStateServer implements pb.RobotStateServiceServer with single-client streaming.
type RobotStateServer struct {
	pb.UnimplementedRobotStateServiceServer

	logger   *slog.Logger
	dataCh   chan *pb.RobotState

	// atomic.Bool provides thread-safe boolean operations without a mutex.
	hasClient atomic.Bool
}

// NewRobotStateServer creates a new RobotStateServer.
func NewRobotStateServer(logger *slog.Logger) *RobotStateServer {
	return &RobotStateServer{
		logger: logger,
		dataCh: make(chan *pb.RobotState, 64),
	}
}

// SubscribeRobotState streams robot state to the client.
// Only one client is allowed at a time.
func (s *RobotStateServer) SubscribeRobotState(
	_ *pb.SubscribeRequest,
	stream pb.RobotStateService_SubscribeRobotStateServer,
) error {
	if !s.hasClient.CompareAndSwap(false, true) {
		return status.Error(codes.AlreadyExists, "a client is already subscribed")
	}
	defer s.hasClient.Store(false)

	s.logger.Info("gRPC client subscribed")

	for {
		select {
		case state, ok := <-s.dataCh:
			if !ok {
				return nil
			}
			if err := stream.Send(state); err != nil {
				s.logger.Warn("gRPC send failed", "error", err)
				return err
			}
		case <-stream.Context().Done():
			s.logger.Info("gRPC client disconnected")
			return stream.Context().Err()
		}
	}
}

// Publish sends a RobotState to the connected client.
// Non-blocking: drops the message if the channel is full.
func (s *RobotStateServer) Publish(state *pb.RobotState) {
	select {
	case s.dataCh <- state:
	default:
	}
}

// DDSToProto converts a DDS RobotState to the proto RobotState.
func DDSToProto(rs *dds.RobotState) *pb.RobotState {
	return &pb.RobotState{
		RobotId:   rs.RobotID,
		RobotName: rs.RobotName,
		Model:     rs.Model,
		Map:       rs.Map,
		Pose: &pb.Pose{
			X:   float32(rs.PoseX),
			Y:   float32(rs.PoseY),
			Yaw: float32(rs.Yaw()),
		},
		Twist: &pb.Twist{
			Vx:    float32(rs.LinearX),
			Vy:    float32(rs.LinearY),
			Omega: float32(rs.AngularZ),
		},
		Battery: &pb.Battery{
			Percentage: rs.BatteryPct,
			Voltage:    rs.BatteryV,
		},
		Timestamp: int64(rs.TimestampSec)*1e9 + int64(rs.TimestampNsec),
	}
}
