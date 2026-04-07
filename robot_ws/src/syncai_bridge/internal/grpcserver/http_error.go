package grpcserver

import (
	"errors"
	"net/http"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	"github.com/nicosyncai/syncai-bridge/internal/restclient"
)

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
