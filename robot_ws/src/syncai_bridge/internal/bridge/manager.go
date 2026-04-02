package bridge

import (
	"fmt"
	"sync"
)

// BridgeInfo is a read-only snapshot of a bridge's state.
type BridgeInfo struct {
	DeviceID string
	Protocol string
	Status   BridgeStatus
}

// Manager is a thread-safe registry for managing bridge instances at runtime.
type Manager struct {
	mu      sync.RWMutex
	bridges map[string]Bridge
}

// NewManager creates an empty BridgeManager.
func NewManager() *Manager {
	return &Manager{
		bridges: make(map[string]Bridge),
	}
}

// Register adds a bridge and optionally connects it.
// Returns error if device_id is already registered or connection fails.
func (m *Manager) Register(b Bridge, connect bool) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	id := b.DeviceID()
	if _, exists := m.bridges[id]; exists {
		return fmt.Errorf("bridge already registered: %s", id)
	}

	if connect {
		if err := b.Connect(); err != nil {
			return fmt.Errorf("failed to connect bridge %s: %w", id, err)
		}
	}

	m.bridges[id] = b
	return nil
}

// Unregister removes a bridge and disconnects it.
func (m *Manager) Unregister(deviceID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	b, exists := m.bridges[deviceID]
	if !exists {
		return fmt.Errorf("bridge not found: %s", deviceID)
	}

	err := b.Disconnect()
	delete(m.bridges, deviceID)
	return err
}

// Get returns the bridge for the given device ID, or nil.
func (m *Manager) Get(deviceID string) Bridge {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.bridges[deviceID]
}

// List returns info about all registered bridges.
func (m *Manager) List() []BridgeInfo {
	m.mu.RLock()
	defer m.mu.RUnlock()

	infos := make([]BridgeInfo, 0, len(m.bridges))
	for _, b := range m.bridges {
		infos = append(infos, BridgeInfo{
			DeviceID: b.DeviceID(),
			Protocol: b.Protocol(),
			Status:   b.Status(),
		})
	}
	return infos
}

// DisconnectAll disconnects and removes all bridges. Used during shutdown.
func (m *Manager) DisconnectAll() {
	m.mu.Lock()
	defer m.mu.Unlock()

	for id, b := range m.bridges {
		_ = b.Disconnect()
		delete(m.bridges, id)
	}
}

// HealthCheckAll returns health status of all bridges.
func (m *Manager) HealthCheckAll() map[string]bool {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make(map[string]bool, len(m.bridges))
	for id, b := range m.bridges {
		result[id] = b.HealthCheck()
	}
	return result
}
