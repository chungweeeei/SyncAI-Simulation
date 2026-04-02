package state

import (
	"sync"

	"github.com/nicosyncai/syncai-bridge/internal/dds"
)

// Store is a thread-safe in-memory cache of the latest RobotState per device.
type Store struct {
	mu     sync.RWMutex
	states map[string]*dds.RobotState
}

func NewStore() *Store {
	return &Store{
		states: make(map[string]*dds.RobotState),
	}
}

func (s *Store) Update(deviceID string, state *dds.RobotState) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.states[deviceID] = state
}

func (s *Store) Get(deviceID string) *dds.RobotState {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.states[deviceID]
}

func (s *Store) GetAll() map[string]*dds.RobotState {
	s.mu.RLock()
	defer s.mu.RUnlock()
	result := make(map[string]*dds.RobotState, len(s.states))
	for k, v := range s.states {
		result[k] = v
	}
	return result
}
