package modbusclient

// ModbusRequest describes a generic modbus coil operation.
type ModbusRequest struct {
	Server  string
	UnitID  uint8
	Address uint16
	Value   bool // used for write_coil
}

// ModbusResponse is the result of a modbus operation.
type ModbusResponse struct {
	Success bool
	Message string
	Value   bool // used for read_coil
}
