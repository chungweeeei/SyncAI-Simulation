package grpcserver

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"

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
	modbusReq := &modbusclient.ModbusRequest{
		Server:  params.GetServer(),
		UnitID:  uint8(params.GetUnitId()),
		Address: uint16(params.GetAddress()),
		Value:   params.GetValue(),
	}

	s.logger.Info("modbus command",
		"device", req.GetDeviceId(),
		"command", req.GetCommand(),
		"server", modbusReq.Server,
		"unit_id", modbusReq.UnitID,
		"address", modbusReq.Address,
	)

	var resp *modbusclient.ModbusResponse
	var err error

	switch req.GetCommand() {
	case "read_coil":
		resp, err = s.modbus.ReadCoil(modbusReq)
	case "write_coil":
		resp, err = s.modbus.WriteCoil(modbusReq)
	case "read_discrete_input":
		resp, err = s.modbus.ReadDiscreteInput(modbusReq)
	default:
		return nil, status.Errorf(codes.InvalidArgument, "unsupported modbus command: %s (expected \"read_coil\", \"write_coil\", or \"read_discrete_input\")", req.GetCommand())
	}

	if err != nil {
		s.logger.Error("modbus command failed", "error", err)
		return nil, mapModbusError(err)
	}

	data, _ := json.Marshal(map[string]any{
		"value": resp.Value,
	})

	return &pb.CommandResponse{
		Success: resp.Success,
		Message: resp.Message,
		Data:    string(data),
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

func mapModbusError(err error) error {
	var mbErr *modbusclient.ModbusError
	if errors.As(err, &mbErr) {
		switch mbErr.Op {
		case "connect":
			return status.Error(codes.Unavailable, mbErr.Detail)
		default:
			return status.Errorf(codes.Internal, "modbus error: %v", mbErr)
		}
	}
	return status.Errorf(codes.Internal, "modbus error: %v", err)
}
