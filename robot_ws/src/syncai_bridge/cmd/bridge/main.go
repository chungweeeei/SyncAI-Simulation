package main

import (
	"encoding/json"
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

	logger.Info("starting syncai-bridge",
		"robot_id", robotID,
		"domain_id", domainID)

	ddsBridge := dds.NewDDSBridge(logger, dds.DDSBridgeConfig{
		DeviceID:  robotID,
		DomainID:  domainID,
		Namespace: robotID,
	})

	ddsBridge.OnData(func(deviceID, dataType string, payload []byte) {
		var rs dds.RobotState
		if err := json.Unmarshal(payload, &rs); err != nil {
			logger.Error("failed to unmarshal robot state", "error", err, "robot_id", robotID)
			return
		}
		logger.Info("robot_state received",
			"robot_id", rs.RobotID,
			"pose_x", rs.PoseX,
			"pose_y", rs.PoseY,
			"battery_pct", rs.BatteryPct,
		)
	})

	if err := ddsBridge.Connect(); err != nil {
		logger.Error("failed to connect DDS bridge", "error", err, "robot_id", robotID)
		os.Exit(1)
	}

	logger.Info("listening for robot_state on DDS topic")

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
