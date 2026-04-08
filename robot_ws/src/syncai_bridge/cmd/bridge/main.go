package main

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"strconv"
	"syscall"

	"github.com/nicosyncai/syncai-bridge/internal/dds"
	"github.com/nicosyncai/syncai-bridge/internal/grpcserver"
	"github.com/nicosyncai/syncai-bridge/internal/modbusclient"
	"github.com/nicosyncai/syncai-bridge/internal/restclient"
)

type config struct {
	RobotID       string
	DomainID      int32
	DDSConfigPath string
	GRPCAddr      string
	RobotAPIURL   string
	ModbusHost    string
	ModbusPort    int
}

func loadConfig() config {
	return config{
		RobotID:       envOr("ROBOT_ID", "robot01"),
		DomainID:      0,
		DDSConfigPath: envOr("CYCLONEDDS_CONFIG", "config/cyclonedds.xml"),
		GRPCAddr:      envOr("GRPC_LISTEN_ADDR", ":50051"),
		RobotAPIURL:   envOr("ROBOT_API_URL", "http://localhost:3001"),
		ModbusHost:    envOr("MODBUS_HOST", "syncai-simulation"),
		ModbusPort:    envIntOr("MODBUS_PORT", 5020),
	}
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := loadConfig()

	logger.Info("starting syncai-bridge",
		"robot_id", cfg.RobotID,
		"domain_id", cfg.DomainID,
		"dds_config", cfg.DDSConfigPath)

	var configXML string
	if data, err := os.ReadFile(cfg.DDSConfigPath); err != nil {
		logger.Warn("could not read CycloneDDS config, using defaults", "path", cfg.DDSConfigPath, "error", err)
	} else {
		configXML = string(data)
		logger.Info("loaded CycloneDDS config", "path", cfg.DDSConfigPath)
	}

	// Start Modbus/REST client.
	modbusClient, err := modbusclient.New(cfg.ModbusHost, cfg.ModbusPort, 1, logger)
	if err != nil {
		logger.Error("failed to create modbus client", "error", err)
		os.Exit(1)
	}
	if err := modbusClient.Connect(); err != nil {
		logger.Error("failed to connect modbus client", "error", err)
		os.Exit(1)
	}
	restClient := restclient.New(cfg.RobotAPIURL, logger)

	// Register gRPC command server with both clients.
	commandServer := grpcserver.NewCommandServer(logger, modbusClient, restClient)

	// Register gRPC robot state server.
	robotStateSrv := grpcserver.NewRobotStateServer(logger)

	gs, err := grpcserver.Start(cfg.GRPCAddr, logger, robotStateSrv, commandServer)
	if err != nil {
		logger.Error("failed to start gRPC server", "error", err)
		os.Exit(1)
	}

	// Start DDS bridge.
	ddsBridge := dds.NewDDSBridge(logger, dds.DDSBridgeConfig{
		DeviceID:  cfg.RobotID,
		DomainID:  cfg.DomainID,
		Namespace: cfg.RobotID,
		ConfigXML: configXML,
	})

	// Forward DDS data to gRPC stream.
	ddsBridge.OnData(func(deviceID, dataType string, payload []byte) {
		if dataType != "robot_state" {
			return
		}
		var rs dds.RobotState
		if err := json.Unmarshal(payload, &rs); err != nil {
			logger.Error("failed to unmarshal robot state", "error", err)
			return
		}
		robotStateSrv.Publish(grpcserver.DDSToProto(&rs))
	})

	if err := ddsBridge.Connect(); err != nil {
		logger.Error("failed to connect DDS bridge", "error", err)
		os.Exit(1)
	}

	// Subscribe to robot_state topic.
	if err := ddsBridge.Subscribe(dds.SubscriptionConfig{
		TopicName:   fmt.Sprintf("rt/%s/robot_state", cfg.RobotID),
		DataType:    "robot_state",
		CreateTopic: dds.CreateRobotStateTopic,
		Take: func(r *dds.DDSReader) (any, error) {
			return dds.TakeRobotState(r)
		},
	}); err != nil {
		logger.Error("failed to subscribe to robot_state", "error", err)
		os.Exit(1)
	}

	logger.Info("listening for DDS topics", "robot_id", cfg.RobotID)

	// Wait for shutdown signal.
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	sig := <-sigCh
	logger.Info("received signal, shutting down", "signal", sig)

	gs.GracefulStop()
	modbusClient.Close()
	ddsBridge.Disconnect()
	logger.Info("shutdown complete")
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func envIntOr(key string, fallback int) int {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return fallback
	}
	return n
}
