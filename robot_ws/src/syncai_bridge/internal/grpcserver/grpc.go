package grpcserver

import (
	"log/slog"
	"net"

	"google.golang.org/grpc"

	pb "github.com/nicosyncai/syncai-bridge/internal/grpcserver/pb"
)

// Start creates a listener and serves gRPC. Returns the server for shutdown.
func Start(addr string, logger *slog.Logger, rsSrv *RobotStateServer, mapSrv *MapServer, taskSrv *TaskServer) (*grpc.Server, error) {
	lis, err := net.Listen("tcp", addr)
	if err != nil {
		return nil, err
	}
	gs := grpc.NewServer()
	pb.RegisterRobotStateServiceServer(gs, rsSrv)
	pb.RegisterMapServiceServer(gs, mapSrv)
	pb.RegisterTaskServiceServer(gs, taskSrv)
	logger.Info("gRPC server listening", "address", addr)
	go gs.Serve(lis)
	return gs, nil
}
