package modbusclient

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"github.com/simonvetter/modbus"
)

const (
	DefaultPollInterval = 250 * time.Millisecond
	DefaultTimeout      = 10 * time.Second
)

// Client is a Modbus TCP client for controlling devices.
type Client struct {
	client *modbus.ModbusClient
	unitID uint8
	logger *slog.Logger
}

// New creates a Modbus TCP client.
func New(host string, port int, unitID uint8, logger *slog.Logger) (*Client, error) {
	url := fmt.Sprintf("tcp://%s:%d", host, port)
	client, err := modbus.NewClient(&modbus.ClientConfiguration{
		URL:     url,
		Timeout: 5 * time.Second,
	})
	if err != nil {
		return nil, fmt.Errorf("create modbus client: %w", err)
	}
	return &Client{
		client: client,
		unitID: unitID,
		logger: logger,
	}, nil
}

// Connect opens the Modbus TCP connection.
func (c *Client) Connect() error {
	if err := c.client.Open(); err != nil {
		return fmt.Errorf("modbus connect: %w", err)
	}
	c.client.SetUnitId(c.unitID)
	c.logger.Info("modbus client connected")
	return nil
}

// Close closes the Modbus TCP connection.
func (c *Client) Close() {
	c.client.Close()
}

// ControlDoor writes a coil to open/close a door, then polls discrete input until confirmed or timeout.
func (c *Client) ControlDoor(ctx context.Context, req *DoorControlRequest) (*DoorControlResponse, error) {
	action := "open"
	if !req.Open {
		action = "close"
	}
	c.logger.Info("controlling door", "action", action, "address", req.Address)

	if err := c.client.WriteCoil(uint16(req.Address), req.Open); err != nil {
		return nil, &ModbusError{Op: "write_coil", Detail: err.Error()}
	}

	timeout := req.TimeoutSec
	if timeout <= 0 {
		timeout = DefaultTimeout
	}

	ticker := time.NewTicker(DefaultPollInterval)
	defer ticker.Stop()

	deadline := time.After(timeout)

	for {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-deadline:
			return &DoorControlResponse{
				Success: false,
				Message: fmt.Sprintf("door %s timed out after %s", action, timeout),
			}, nil
		case <-ticker.C:
			state, err := c.client.ReadDiscreteInput(uint16(req.Address))
			if err != nil {
				return nil, &ModbusError{Op: "read_discrete_input", Detail: err.Error()}
			}
			if state == req.Open {
				return &DoorControlResponse{
					Success: true,
					Message: fmt.Sprintf("door %sed successfully", action),
				}, nil
			}
		}
	}
}
