package grpcserver

import (
	"context"
	"log/slog"

	pb "github.com/nicosyncai/syncai-bridge/internal/grpcserver/pb"
	"github.com/nicosyncai/syncai-bridge/internal/restclient"
)

// MapServer implements pb.MapServiceServer by proxying to the robot REST API.
type MapServer struct {
	pb.UnimplementedMapServiceServer

	logger *slog.Logger
	rest   *restclient.Client
}

// NewMapServer creates a new MapServer.
func NewMapServer(logger *slog.Logger, rest *restclient.Client) *MapServer {
	return &MapServer{
		logger: logger,
		rest:   rest,
	}
}

// GetMap fetches the map from the robot REST API.
func (s *MapServer) GetMap(ctx context.Context, _ *pb.GetMapRequest) (*pb.MapResponse, error) {
	payload, err := s.rest.GetMap(ctx)
	if err != nil {
		s.logger.Error("GetMap failed", "error", err)
		return nil, mapHTTPError(err)
	}

	origin := &pb.MapPose{
		X:   float32(payload.MapMetadata.Origin.X),
		Y:   float32(payload.MapMetadata.Origin.Y),
		Yaw: float32(payload.MapMetadata.Origin.Theta),
	}

	vertexes := make([]*pb.Vertex, len(payload.Vertexes))
	for i, v := range payload.Vertexes {
		vertexes[i] = &pb.Vertex{
			Name: v.Name,
			Pose: &pb.MapPose{
				X:   float32(v.Pose.X),
				Y:   float32(v.Pose.Y),
				Yaw: float32(v.Pose.Theta),
			},
		}
	}

	return &pb.MapResponse{
		MapMetadata: &pb.MapMetadata{
			MapId:      payload.MapMetadata.MapID,
			Resolution: float32(payload.MapMetadata.Resolution),
			Width:      uint32(payload.MapMetadata.Width),
			Height:     uint32(payload.MapMetadata.Height),
			Origin:     origin,
		},
		Vertexes: vertexes,
	}, nil
}

