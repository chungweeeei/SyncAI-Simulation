import re
import time
from typing import Optional, Tuple

import structlog
from pymodbus.client import ModbusTcpClient


POLL_INTERVAL_SEC = 0.25
CONVEYOR_BASE_IR = 10
PHASE_CARRIED = 3
PHASE_DROPPED = 4

# Mirrors sim_ws/syncai_modbus_server: IR[50 + i*4 .. +4] holds box_id for conveyor index i.
# Phase enum at IR[10..19]; box_id moved to 50 to avoid collision.
CONVEYOR_BOX_ID_IR_BASE = 50
CONVEYOR_BOX_ID_IR_WIDTH = 4


class ModbusGateway:

    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger,
        host: str = "127.0.0.1",
        port: int = 5020,
        unit_id: int = 1,
    ):
        self._logger = logger
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._client = ModbusTcpClient(host=host, port=port)

        if self._client.connect():
            logger.info("[ModbusGateway] Connected", host=host, port=port)
        else:
            logger.warning("[ModbusGateway] Initial connection failed", host=host, port=port)

    def control_door(
        self,
        cmd_topic: str,
        open: bool = True,
        timeout_sec: float = 10.0,
        coil_address: Optional[int] = None,
    ) -> Tuple[bool, str]:
        if coil_address is None:
            coil_address = self._parse_coil_address(cmd_topic)

        action_str = "open" if open else "close"
        self._logger.info(
            f"[ModbusGateway] Door {action_str}",
            coil_address=coil_address,
        )

        if not self._client.connected:
            if not self._client.connect():
                return False, "Modbus TCP connection failed"

        result = self._client.write_coil(coil_address, open, device_id=self._unit_id)
        if result.isError():
            return False, f"Modbus write_coil failed: {result}"

        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            resp = self._client.read_discrete_inputs(coil_address, count=1, device_id=self._unit_id)
            if resp.isError():
                return False, f"Modbus read_discrete_inputs failed: {resp}"

            current_state = resp.bits[0]
            if current_state == open:
                return True, f"Door {'opened' if open else 'closed'} successfully"

            time.sleep(POLL_INTERVAL_SEC)

        return False, f"Door {action_str} timed out after {timeout_sec}s"

    def read_conveyor_box_id(self, conveyor_id: str) -> Tuple[bool, str, str]:
        ir_address = self._parse_conveyor_box_id_ir_address(conveyor_id)
        self._logger.info(
            "[ModbusGateway] read_conveyor_box_id",
            conveyor=conveyor_id,
            ir_address=ir_address,
        )

        if not self._client.connected:
            if not self._client.connect():
                return False, "Modbus TCP connection failed", ""

        resp = self._client.read_input_registers(
            ir_address, count=CONVEYOR_BOX_ID_IR_WIDTH, device_id=self._unit_id
        )
        if resp.isError():
            return False, f"Modbus read_input_registers failed: {resp}", ""

        chars = bytearray()
        for reg in resp.registers:
            chars.append((reg >> 8) & 0xFF)
            chars.append(reg & 0xFF)
        box_id = chars.rstrip(b"\x00").decode("ascii", errors="replace")
        if not box_id:
            return False, f"conveyor {conveyor_id} has no box_id at IR[{ir_address}]", ""
        return True, f"read box_id={box_id} from {conveyor_id}", box_id

    def verify_pickup(
        self,
        conveyor_id: str,
        timeout_sec: float = 10.0,
    ) -> Tuple[bool, str]:
        ir_address = self._parse_conveyor_ir_address(conveyor_id)
        self._logger.info(
            "[ModbusGateway] verify_pickup",
            conveyor=conveyor_id,
            ir_address=ir_address,
            timeout_sec=timeout_sec,
        )

        if not self._client.connected:
            if not self._client.connect():
                return False, "Modbus TCP connection failed"

        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            resp = self._client.read_input_registers(
                ir_address, count=1, device_id=self._unit_id
            )
            if resp.isError():
                return False, f"Modbus read_input_registers failed: {resp}"

            if resp.registers[0] == PHASE_CARRIED:
                return True, f"conveyor {conveyor_id} phase=carried"

            time.sleep(POLL_INTERVAL_SEC)

        return False, f"pickup verify timed out after {timeout_sec}s"

    def verify_dropoff(
        self,
        conveyor_id: str,
        timeout_sec: float = 10.0,
    ) -> Tuple[bool, str]:
        ir_address = self._parse_conveyor_ir_address(conveyor_id)
        self._logger.info(
            "[ModbusGateway] verify_dropoff",
            conveyor=conveyor_id,
            ir_address=ir_address,
            timeout_sec=timeout_sec,
        )

        if not self._client.connected:
            if not self._client.connect():
                return False, "Modbus TCP connection failed"

        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            resp = self._client.read_input_registers(
                ir_address, count=1, device_id=self._unit_id
            )
            if resp.isError():
                return False, f"Modbus read_input_registers failed: {resp}"

            if resp.registers[0] == PHASE_DROPPED:
                return True, f"conveyor {conveyor_id} phase=dropped"

            time.sleep(POLL_INTERVAL_SEC)

        return False, f"dropoff verify timed out after {timeout_sec}s"

    @staticmethod
    def _parse_coil_address(cmd_topic: str) -> int:
        match = re.search(r"door_(\d+)", cmd_topic)
        if not match:
            raise ValueError(f"Cannot parse door ID from topic: {cmd_topic}")
        return int(match.group(1)) - 1  # door_01 -> 0, door_02 -> 1

    @staticmethod
    def _parse_conveyor_ir_address(conveyor_id: str) -> int:
        match = re.search(r"conveyor_(\d+)", conveyor_id)
        if not match:
            raise ValueError(f"Cannot parse conveyor id: {conveyor_id}")
        return CONVEYOR_BASE_IR + (int(match.group(1)) - 1)  # conveyor_01 -> 10

    @staticmethod
    def _parse_conveyor_box_id_ir_address(conveyor_id: str) -> int:
        match = re.search(r"conveyor_(\d+)", conveyor_id)
        if not match:
            raise ValueError(f"Cannot parse conveyor id: {conveyor_id}")
        return CONVEYOR_BOX_ID_IR_BASE + (int(match.group(1)) - 1) * CONVEYOR_BOX_ID_IR_WIDTH

    def close(self):
        self._client.close()
