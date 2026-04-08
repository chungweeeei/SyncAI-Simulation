package modbusclient

import "fmt"

// ModbusError represents an error from a Modbus operation.
type ModbusError struct {
	Op     string
	Detail string
}

func (e *ModbusError) Error() string {
	return fmt.Sprintf("modbus %s: %s", e.Op, e.Detail)
}
