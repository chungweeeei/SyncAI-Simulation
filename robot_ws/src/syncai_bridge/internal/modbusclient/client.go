package modbusclient

import (
	"fmt"
	"log/slog"
	"sync"
	"time"

	"github.com/simonvetter/modbus"
)

const (
	DefaultTimeout = 10 * time.Second
)

// Client is a Modbus TCP client that manages connections dynamically by server address.
type Client struct {
	mu      sync.Mutex
	clients map[string]*modbus.ModbusClient
	logger  *slog.Logger
}

// New creates a Modbus TCP client manager.
func New(logger *slog.Logger) *Client {
	return &Client{
		clients: make(map[string]*modbus.ModbusClient),
		logger:  logger,
	}
}

// getOrConnect returns a cached modbus connection or creates a new one.
func (c *Client) getOrConnect(server string, unitID uint8) (*modbus.ModbusClient, error) {
	key := fmt.Sprintf("%s/%d", server, unitID)

	c.mu.Lock()
	defer c.mu.Unlock()

	if client, ok := c.clients[key]; ok {
		return client, nil
	}

	url := fmt.Sprintf("tcp://%s", server)
	client, err := modbus.NewClient(&modbus.ClientConfiguration{
		URL:     url,
		Timeout: 5 * time.Second,
	})
	if err != nil {
		return nil, fmt.Errorf("create modbus client: %w", err)
	}

	if err := client.Open(); err != nil {
		return nil, fmt.Errorf("modbus connect to %s: %w", server, err)
	}

	client.SetUnitId(unitID)
	c.clients[key] = client
	c.logger.Info("modbus client connected", "server", server, "unit_id", unitID)

	return client, nil
}

// ReadCoil reads a single coil from the specified modbus server.
func (c *Client) ReadCoil(req *ModbusRequest) (*ModbusResponse, error) {
	client, err := c.getOrConnect(req.Server, req.UnitID)
	if err != nil {
		return nil, &ModbusError{Op: "connect", Detail: err.Error()}
	}

	value, err := client.ReadCoil(req.Address)
	if err != nil {
		return nil, &ModbusError{Op: "read_coil", Detail: err.Error()}
	}

	return &ModbusResponse{
		Success: true,
		Message: fmt.Sprintf("read coil %d: %v", req.Address, value),
		Value:   value,
	}, nil
}

// WriteCoil writes a single coil to the specified modbus server.
func (c *Client) WriteCoil(req *ModbusRequest) (*ModbusResponse, error) {
	client, err := c.getOrConnect(req.Server, req.UnitID)
	if err != nil {
		return nil, &ModbusError{Op: "connect", Detail: err.Error()}
	}

	if err := client.WriteCoil(req.Address, req.Value); err != nil {
		return nil, &ModbusError{Op: "write_coil", Detail: err.Error()}
	}

	return &ModbusResponse{
		Success: true,
		Message: fmt.Sprintf("write coil %d = %v", req.Address, req.Value),
		Value:   req.Value,
	}, nil
}

// ReadDiscreteInput reads a single discrete input from the specified modbus server.
func (c *Client) ReadDiscreteInput(req *ModbusRequest) (*ModbusResponse, error) {
	client, err := c.getOrConnect(req.Server, req.UnitID)
	if err != nil {
		return nil, &ModbusError{Op: "connect", Detail: err.Error()}
	}

	value, err := client.ReadDiscreteInput(req.Address)
	if err != nil {
		return nil, &ModbusError{Op: "read_discrete_input", Detail: err.Error()}
	}

	return &ModbusResponse{
		Success: true,
		Message: fmt.Sprintf("read discrete input %d: %v", req.Address, value),
		Value:   value,
	}, nil
}

// Close closes all cached modbus connections.
func (c *Client) Close() {
	c.mu.Lock()
	defer c.mu.Unlock()

	for key, client := range c.clients {
		client.Close()
		delete(c.clients, key)
	}
}
