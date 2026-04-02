package bridge

import (
	"sync"
)

// BridgeStatus represents the current connection state of a bridge.
type BridgeStatus string

const (
	Disconnected BridgeStatus = "disconnected"
	Connecting   BridgeStatus = "connecting"
	Connected    BridgeStatus = "connected"
	Error        BridgeStatus = "error"
)

// DataCallback is invoked when inbound data arrives from a device.
// deviceID identifies the source, dataType describes the data (e.g. "robot_state"),
// and payload contains the JSON-encoded domain model.
type DataCallback func(deviceID string, dataType string, payload []byte)

// Bridge is the protocol abstraction interface.
// Each protocol (DDS, MQTT, MODBUS, etc.) implements this interface.
type Bridge interface {
	Connect() error
	Disconnect() error
	Status() BridgeStatus
	DeviceID() string
	Protocol() string
	OnData(callback DataCallback)
	HealthCheck() bool
}

// BaseBridge provides shared fields and helpers for Bridge implementations.
type BaseBridge struct {
	deviceID  string
	protocol  string
	status    BridgeStatus
	statusMu  sync.RWMutex
	callbacks []DataCallback
	callbackMu sync.RWMutex
}

// NewBaseBridge creates a BaseBridge with initial disconnected status.
func NewBaseBridge(deviceID, protocol string) BaseBridge {
	return BaseBridge{
		deviceID: deviceID,
		protocol: protocol,
		status:   Disconnected,
	}
}

func (b *BaseBridge) DeviceID() string { return b.deviceID }
func (b *BaseBridge) Protocol() string { return b.protocol }

func (b *BaseBridge) Status() BridgeStatus {
	b.statusMu.RLock()
	defer b.statusMu.RUnlock()
	return b.status
}

func (b *BaseBridge) SetStatus(s BridgeStatus) {
	b.statusMu.Lock()
	defer b.statusMu.Unlock()
	b.status = s
}

func (b *BaseBridge) OnData(callback DataCallback) {
	b.callbackMu.Lock()
	defer b.callbackMu.Unlock()
	b.callbacks = append(b.callbacks, callback)
}

// EmitData calls all registered callbacks with the given data.
// Panics in individual callbacks are recovered to avoid crashing the bridge.
func (b *BaseBridge) EmitData(deviceID, dataType string, payload []byte) {
	b.callbackMu.RLock()
	defer b.callbackMu.RUnlock()
	for _, cb := range b.callbacks {
		func() {
			defer func() {
				if r := recover(); r != nil {
					// Log recovered panic — in production, use structured logger
				}
			}()
			cb(deviceID, dataType, payload)
		}()
	}
}
