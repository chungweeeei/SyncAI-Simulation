package main

import (
	"context"
	"encoding/json"
	"log/slog"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/nicosyncai/syncai-bridge/internal/bridge"
	"github.com/nicosyncai/syncai-bridge/internal/dds"
	"github.com/nicosyncai/syncai-bridge/internal/dispatch"
	"github.com/nicosyncai/syncai-bridge/internal/httpapi"
	"github.com/nicosyncai/syncai-bridge/internal/state"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))

	robots := parseRobots(envOr("BRIDGE_ROBOTS", "robot01"))
	domainID := int32(0)
	httpAddr := envOr("BRIDGE_HTTP_ADDR", ":8080")

	logger.Info("starting syncai-bridge",
		"robots", robots,
		"domain_id", domainID,
		"http_addr", httpAddr)

	// State store (aggregates all robot states)
	store := state.NewStore()

	// Shared DDS participant for outbound writes
	participant, err := dds.CreateParticipant(domainID)
	if err != nil {
		logger.Error("failed to create DDS participant", "error", err)
		os.Exit(1)
	}

	// Per-robot DDS listeners (upstream: robot_state → store)
	manager := bridge.NewManager()
	for _, robotID := range robots {
		ddsBridge := dds.NewDDSBridge(logger, dds.DDSBridgeConfig{
			DeviceID:  robotID,
			DomainID:  domainID,
			Namespace: robotID,
		})

		rid := robotID // capture for closure
		ddsBridge.OnData(func(deviceID, dataType string, payload []byte) {
			var rs dds.RobotState
			if err := json.Unmarshal(payload, &rs); err != nil {
				logger.Error("failed to unmarshal robot state", "error", err, "device_id", rid)
				return
			}
			store.Update(rid, &rs)
			logger.Debug("state updated", "device_id", rid)
		})

		if err := manager.Register(ddsBridge, true); err != nil {
			logger.Error("failed to register DDS bridge", "error", err, "robot_id", robotID)
			os.Exit(1)
		}
	}

	// DDS outbound adapter (downstream: dispatch → cmd_vel)
	ddsAdapter := dds.NewAdapter(logger, participant)

	// Router
	router := dispatch.NewRouter()
	router.Register(ddsAdapter)

	// HTTP server
	httpServer := httpapi.NewServer(httpAddr, store, router, logger)
	go func() {
		if err := httpServer.Start(); err != nil {
			logger.Error("HTTP server error", "error", err)
		}
	}()

	// Wait for shutdown signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	sig := <-sigCh
	logger.Info("received signal, shutting down", "signal", sig)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	httpServer.Shutdown(ctx)
	ddsAdapter.Stop()
	manager.DisconnectAll()
	logger.Info("shutdown complete")
}

func parseRobots(s string) []string {
	parts := strings.Split(s, ",")
	robots := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			robots = append(robots, p)
		}
	}
	return robots
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
