package dds

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"sync"

	"github.com/nicosyncai/syncai-bridge/internal/bridge"
)

// TopicCreateFn creates a DDS topic on the given participant.
type TopicCreateFn func(p *DDSParticipant, topicName string) (*DDSTopic, error)

// TakeFn takes one sample from the reader and returns a Go domain object.
// Returns (nil, nil) when no more data is available.
type TakeFn func(r *DDSReader) (any, error)

// SubscriptionConfig defines what to subscribe to and how to deserialize it.
type SubscriptionConfig struct {
	TopicName   string       // DDS topic name, e.g. "rt/robot01/robot_state"
	DataType    string       // logical data type, e.g. "robot_state"
	CreateTopic TopicCreateFn
	Take        TakeFn
}

// subscription holds the DDS entities for a single topic subscription.
type subscription struct {
	config SubscriptionConfig
	topic  *DDSTopic
	reader *DDSReader
}

// DDSBridgeConfig holds configuration for a DDS bridge.
type DDSBridgeConfig struct {
	DeviceID  string
	DomainID  int32
	Namespace string // ROS 2 namespace, e.g. "robot01"
	ConfigXML string // CycloneDDS XML configuration; empty means use env/defaults
}

// DDSBridge implements Bridge for CycloneDDS.
type DDSBridge struct {
	bridge.BaseBridge

	config        DDSBridgeConfig
	logger        *slog.Logger
	participant   *DDSParticipant
	subscriptions map[int32]*subscription // reader handle → subscription
	mu            sync.Mutex
}

// NewDDSBridge creates a new DDS bridge.
func NewDDSBridge(logger *slog.Logger, config DDSBridgeConfig) *DDSBridge {
	return &DDSBridge{
		BaseBridge:    bridge.NewBaseBridge(config.DeviceID, "dds"),
		config:        config,
		logger:        logger,
		subscriptions: make(map[int32]*subscription),
	}
}

// Connect creates the DDS participant.
func (b *DDSBridge) Connect() error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if b.Status() == bridge.Connected {
		return nil
	}
	b.SetStatus(bridge.Connecting)

	b.logger.Info("connecting DDS bridge",
		"device_id", b.config.DeviceID,
		"domain_id", b.config.DomainID)

	participant, err := CreateParticipant(b.config.DomainID, b.config.ConfigXML)
	if err != nil {
		b.SetStatus(bridge.Error)
		return fmt.Errorf("create participant: %w", err)
	}
	b.participant = participant

	b.SetStatus(bridge.Connected)
	b.logger.Info("DDS bridge connected", "device_id", b.config.DeviceID)
	return nil
}

// Subscribe creates a topic and reader for the given configuration.
// Must be called after Connect.
func (b *DDSBridge) Subscribe(cfg SubscriptionConfig) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if b.participant == nil {
		return fmt.Errorf("bridge not connected")
	}

	b.logger.Info("subscribing to DDS topic",
		"topic", cfg.TopicName,
		"data_type", cfg.DataType)

	topic, err := cfg.CreateTopic(b.participant, cfg.TopicName)
	if err != nil {
		return fmt.Errorf("create topic %q: %w", cfg.TopicName, err)
	}

	reader, err := CreateReaderWithListener(b.participant, topic)
	if err != nil {
		return fmt.Errorf("create reader for %q: %w", cfg.TopicName, err)
	}

	sub := &subscription{
		config: cfg,
		topic:  topic,
		reader: reader,
	}

	handle := reader.ReaderHandle()
	b.subscriptions[handle] = sub

	// Register in global registry so the C callback can find us.
	readerRegistryMu.Lock()
	readerRegistry[handle] = b
	readerRegistryMu.Unlock()

	b.logger.Info("subscribed to DDS topic",
		"topic", cfg.TopicName,
		"data_type", cfg.DataType,
		"reader_handle", handle)
	return nil
}

// Disconnect tears down all subscriptions and the DDS participant.
func (b *DDSBridge) Disconnect() error {
	b.mu.Lock()
	defer b.mu.Unlock()

	// Unregister all readers from global registry.
	readerRegistryMu.Lock()
	for handle := range b.subscriptions {
		delete(readerRegistry, handle)
	}
	readerRegistryMu.Unlock()

	// Deleting the participant cascades to all topics and readers.
	if b.participant != nil {
		if err := DeleteEntity(b.participant.ParticipantHandle()); err != nil {
			b.SetStatus(bridge.Error)
			return fmt.Errorf("delete participant: %w", err)
		}
	}

	b.participant = nil
	b.subscriptions = make(map[int32]*subscription)
	b.SetStatus(bridge.Disconnected)
	b.logger.Info("DDS bridge disconnected", "device_id", b.config.DeviceID)
	return nil
}

// onDataAvailable is called by goOnDataAvailable when the CycloneDDS
// listener fires. It runs on the CycloneDDS internal thread via CGo.
func (b *DDSBridge) onDataAvailable(readerHandle int32) {
	b.mu.Lock()
	sub, ok := b.subscriptions[readerHandle]
	b.mu.Unlock()
	if !ok {
		return
	}

	for {
		data, err := sub.config.Take(sub.reader)
		if err != nil {
			b.logger.Error("take failed",
				"topic", sub.config.TopicName,
				"error", err)
			return
		}
		if data == nil {
			return // no more data
		}

		payload, err := json.Marshal(data)
		if err != nil {
			b.logger.Error("marshal failed",
				"topic", sub.config.TopicName,
				"error", err)
			continue
		}

		b.EmitData(b.config.DeviceID, sub.config.DataType, payload)
	}
}
