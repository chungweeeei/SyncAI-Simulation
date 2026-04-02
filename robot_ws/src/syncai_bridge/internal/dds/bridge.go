package dds

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"sync"

	"github.com/nicosyncai/syncai-bridge/internal/bridge"
)

// DDSBridgeConfig holds configuration for a DDS bridge.
type DDSBridgeConfig struct {
	DeviceID  string
	DomainID  int32
	TopicName string // ROS 2 DDS topic name, e.g. "rt/robot01/robot_state"
	Namespace string // ROS 2 namespace, e.g. "robot01"
}

// DDSBridge implements Bridge for CycloneDDS.
type DDSBridge struct {
	bridge.BaseBridge

	config      DDSBridgeConfig
	logger      *slog.Logger
	participant *DDSParticipant
	topic       *DDSTopic
	reader      *DDSReader
	mu          sync.Mutex
}

// NewDDSBridge creates a new DDS bridge.
func NewDDSBridge(logger *slog.Logger, config DDSBridgeConfig) *DDSBridge {
	topicName := config.TopicName
	if topicName == "" {
		// Default: ROS 2 DDS topic name convention
		topicName = fmt.Sprintf("rt/%s/robot_state", config.Namespace)
	}
	config.TopicName = topicName

	return &DDSBridge{
		BaseBridge: bridge.NewBaseBridge(config.DeviceID, "dds"),
		config:     config,
		logger:     logger,
	}
}

// Connect creates the DDS participant, topic, and reader with a listener.
func (b *DDSBridge) Connect() error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if b.Status() == bridge.Connected {
		return nil
	}
	b.SetStatus(bridge.Connecting)

	b.logger.Info("connecting DDS bridge",
		"device_id", b.config.DeviceID,
		"domain_id", b.config.DomainID,
		"topic", b.config.TopicName)

	participant, err := CreateParticipant(b.config.DomainID)
	if err != nil {
		b.SetStatus(bridge.Error)
		return fmt.Errorf("create participant: %w", err)
	}
	b.participant = participant

	topic, err := CreateRobotStateTopic(participant, b.config.TopicName)
	if err != nil {
		b.SetStatus(bridge.Error)
		_ = DeleteEntity(participant.ParticipantHandle())
		return fmt.Errorf("create topic: %w", err)
	}
	b.topic = topic

	reader, err := CreateReaderWithListener(participant, topic)
	if err != nil {
		b.SetStatus(bridge.Error)
		_ = DeleteEntity(participant.ParticipantHandle())
		return fmt.Errorf("create reader: %w", err)
	}
	b.reader = reader

	// Register in global registry so the C callback can find us.
	readerRegistryMu.Lock()
	readerRegistry[reader.ReaderHandle()] = b
	readerRegistryMu.Unlock()

	b.SetStatus(bridge.Connected)
	b.logger.Info("DDS bridge connected",
		"device_id", b.config.DeviceID,
		"topic", b.config.TopicName)
	return nil
}

// Disconnect tears down DDS entities.
func (b *DDSBridge) Disconnect() error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if b.reader != nil {
		readerRegistryMu.Lock()
		delete(readerRegistry, b.reader.ReaderHandle())
		readerRegistryMu.Unlock()
	}

	// Deleting the participant cascades to topic and reader.
	if b.participant != nil {
		if err := DeleteEntity(b.participant.ParticipantHandle()); err != nil {
			b.SetStatus(bridge.Error)
			return fmt.Errorf("delete participant: %w", err)
		}
	}

	b.participant = nil
	b.topic = nil
	b.reader = nil
	b.SetStatus(bridge.Disconnected)
	b.logger.Info("DDS bridge disconnected", "device_id", b.config.DeviceID)
	return nil
}

// HealthCheck returns true if the bridge is connected.
func (b *DDSBridge) HealthCheck() bool {
	return b.Status() == bridge.Connected
}

// onDataAvailable is called by goOnDataAvailable when the CycloneDDS
// listener fires. It runs on the CycloneDDS internal thread via CGo.
func (b *DDSBridge) onDataAvailable() {
	if b.reader == nil {
		return
	}

	for {
		state, err := TakeRobotState(b.reader)
		if err != nil {
			b.logger.Error("take robot state failed", "error", err)
			return
		}
		if state == nil {
			return // no more data
		}

		payload, err := json.Marshal(state)
		if err != nil {
			b.logger.Error("marshal robot state failed", "error", err)
			continue
		}

		b.EmitData(b.config.DeviceID, "robot_state", payload)
	}
}
