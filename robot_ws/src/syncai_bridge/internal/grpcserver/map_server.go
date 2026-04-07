package grpcserver

import (
	"context"
	"errors"
	"log/slog"
	"net/http"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

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

// mapHTTPError converts a rest client error to a gRPC status error.
func mapHTTPError(err error) error {
	var httpErr *restclient.HTTPError
	if !errors.As(err, &httpErr) {
		return status.Errorf(codes.Internal, "robot API error: %v", err)
	}
	switch httpErr.StatusCode {
	case http.StatusNotFound:
		return status.Error(codes.NotFound, httpErr.Detail)
	case http.StatusServiceUnavailable:
		return status.Error(codes.Unavailable, httpErr.Detail)
	case http.StatusConflict:
		return status.Error(codes.AlreadyExists, httpErr.Detail)
	case http.StatusBadRequest:
		return status.Error(codes.InvalidArgument, httpErr.Detail)
	default:
		return status.Errorf(codes.Internal, "robot API returned %d: %s", httpErr.StatusCode, httpErr.Detail)
	}
}
