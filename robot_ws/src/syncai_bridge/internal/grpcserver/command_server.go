package grpcserver

import (
	"context"
	"errors"
	"log/slog"
	"time"

	pb "github.com/nicosyncai/syncai-bridge/internal/grpcserver/pb"
	"github.com/nicosyncai/syncai-bridge/internal/modbusclient"
	"github.com/nicosyncai/syncai-bridge/internal/restclient"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// CommandServer implements pb.CommandServiceServer, dispatching to protocol-specific clients.
type CommandServer struct {
	pb.UnimplementedCommandServiceServer

	logger *slog.Logger
	modbus *modbusclient.Client
	rest   *restclient.Client
}

// NewCommandServer creates a CommandServer with the given protocol clients.
func NewCommandServer(logger *slog.Logger, modbus *modbusclient.Client, rest *restclient.Client) *CommandServer {
	return &CommandServer{
		logger: logger,
		modbus: modbus,
		rest:   rest,
	}
}

// SendCommand dispatches a command to the appropriate protocol client.
func (s *CommandServer) SendCommand(ctx context.Context, req *pb.CommandRequest) (*pb.CommandResponse, error) {
	switch p := req.GetProtocol().(type) {
	case *pb.CommandRequest_Modbus:
		return s.handleModbus(ctx, req, p.Modbus)
	case *pb.CommandRequest_Rest:
		return s.handleRest(ctx, p.Rest)
	default:
		return nil, status.Error(codes.InvalidArgument, "protocol is required (modbus or rest)")
	}
}

func (s *CommandServer) handleModbus(ctx context.Context, req *pb.CommandRequest, params *pb.ModbusParams) (*pb.CommandResponse, error) {
	open, err := parseCommand(req.GetCommand())
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, err.Error())
	}

	timeout := time.Duration(req.GetTimeoutSec()) * time.Second
	if timeout <= 0 {
		timeout = modbusclient.DefaultTimeout
	}

	if params.GetUnitId() > 0 {
		s.logger.Info("modbus command", "device", req.GetDeviceId(), "command", req.GetCommand(), "address", params.GetAddress(), "unit_id", params.GetUnitId())
	}

	resp, err := s.modbus.ControlDoor(ctx, &modbusclient.DoorControlRequest{
		Address:    int(params.GetAddress()),
		Open:       open,
		TimeoutSec: timeout,
	})
	if err != nil {
		s.logger.Error("modbus command failed", "error", err)
		return nil, mapModbusError(err)
	}

	return &pb.CommandResponse{
		Success: resp.Success,
		Message: resp.Message,
	}, nil
}

func (s *CommandServer) handleRest(ctx context.Context, params *pb.RestParams) (*pb.CommandResponse, error) {
	data, err := s.rest.SendRequest(ctx, params.GetMethod(), params.GetPath(), params.GetBody())
	if err != nil {
		s.logger.Error("rest command failed", "error", err)
		return nil, mapHTTPError(err)
	}

	return &pb.CommandResponse{
		Success: true,
		Message: "ok",
		Data:    string(data),
	}, nil
}

func parseCommand(cmd string) (bool, error) {
	switch cmd {
	case "open":
		return true, nil
	case "close":
		return false, nil
	default:
		return false, errors.New("unsupported command: " + cmd + " (expected \"open\" or \"close\")")
	}
}

func mapModbusError(err error) error {
	var mbErr *modbusclient.ModbusError
	if errors.As(err, &mbErr) {
		switch mbErr.Op {
		case "parse_address":
			return status.Error(codes.InvalidArgument, mbErr.Detail)
		default:
			return status.Errorf(codes.Internal, "modbus error: %v", mbErr)
		}
	}
	return status.Errorf(codes.Internal, "modbus error: %v", err)
}
