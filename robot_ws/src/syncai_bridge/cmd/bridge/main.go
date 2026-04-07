package main

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/nicosyncai/syncai-bridge/internal/dds"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))

	robotID := envOr("ROBOT_ID", "robot01")
	domainID := int32(0)
	ddsConfigPath := envOr("CYCLONEDDS_CONFIG", "config/cyclonedds.xml")

	logger.Info("starting syncai-bridge",
		"robot_id", robotID,
		"domain_id", domainID,
		"dds_config", ddsConfigPath)

	var configXML string
	if data, err := os.ReadFile(ddsConfigPath); err != nil {
		logger.Warn("could not read CycloneDDS config, using defaults", "path", ddsConfigPath, "error", err)
	} else {
		configXML = string(data)
		logger.Info("loaded CycloneDDS config", "path", ddsConfigPath)
	}

	ddsBridge := dds.NewDDSBridge(logger, dds.DDSBridgeConfig{
		DeviceID:  robotID,
		DomainID:  domainID,
		Namespace: robotID,
		ConfigXML: configXML,
	})

	ddsBridge.OnData(func(deviceID, dataType string, payload []byte) {
		switch dataType {
		case "robot_state":
			var rs dds.RobotState
			if err := json.Unmarshal(payload, &rs); err != nil {
				logger.Error("failed to unmarshal robot state", "error", err)
				return
			}
			logger.Info("robot_state received",
				"robot_id", rs.RobotID,
				"pose_x", rs.PoseX,
				"pose_y", rs.PoseY,
				"battery_pct", rs.BatteryPct,
			)
		default:
			logger.Info("data received",
				"device_id", deviceID,
				"data_type", dataType,
				"size", len(payload),
			)
		}
	})

	if err := ddsBridge.Connect(); err != nil {
		logger.Error("failed to connect DDS bridge", "error", err)
		os.Exit(1)
	}

	// Subscribe to robot_state topic.
	if err := ddsBridge.Subscribe(dds.SubscriptionConfig{
		TopicName:   fmt.Sprintf("rt/%s/robot_state", robotID),
		DataType:    "robot_state",
		CreateTopic: dds.CreateRobotStateTopic,
		Take: func(r *dds.DDSReader) (any, error) {
			return dds.TakeRobotState(r)
		},
	}); err != nil {
		logger.Error("failed to subscribe to robot_state", "error", err)
		os.Exit(1)
	}

	logger.Info("listening for DDS topics", "robot_id", robotID)

	// Wait for shutdown signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	sig := <-sigCh
	logger.Info("received signal, shutting down", "signal", sig)

	ddsBridge.Disconnect()
	logger.Info("shutdown complete")
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
