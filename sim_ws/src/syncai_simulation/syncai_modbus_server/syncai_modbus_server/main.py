import os
import threading

import yaml

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String
from ament_index_python.packages import get_package_share_directory

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartTcpServer

from syncai_modbus_server.datablock import WriteCallbackDataBlock
from syncai_modbus_server.subscribers.door_subscriber import init_door_subscriber
from syncai_modbus_server.subscribers.conveyor_subscriber import init_conveyor_subscriber


CONVEYOR_BASE = 10
MAX_DEVICES_PER_TYPE = 10


class ModbusServerNode(Node):

    def __init__(self):
        super().__init__('modbus_server')

        self.declare_parameter('host', '127.0.0.1')
        self.declare_parameter('port', 5020)
        self.declare_parameter('unit_id', 1)
        self.declare_parameter('config_file', '')
        self.declare_parameter('conveyor_default_speed', 0.5)

        self._host = self.get_parameter('host').value
        self._port = self.get_parameter('port').value
        self._unit_id = self.get_parameter('unit_id').value
        self._conveyor_default_speed = float(
            self.get_parameter('conveyor_default_speed').value
        )

        self._door_ids, self._conveyor_ids = self._load_devices(
            self.get_parameter('config_file').value
        )

        # Door publishers: coil address -> publisher
        self._door_publishers: dict[int, object] = {}
        # Conveyor publishers keyed by index 10..19 (shared by coil/HR/DI for the same conveyor).
        self._conveyor_publishers: dict[int, object] = {}

        # Coils: 0..9 doors, 10..19 conveyor on/off (writes a fixed default speed).
        self._coil_block = WriteCallbackDataBlock(
            0,
            [False] * (CONVEYOR_BASE + MAX_DEVICES_PER_TYPE),
            write_callback=self._on_coil_write,
        )

        # Discrete Inputs: 0..9 doors, 10..19 conveyors. Updated by ROS subscribers.
        self._di_block = ModbusSequentialDataBlock(
            0, [False] * (CONVEYOR_BASE + MAX_DEVICES_PER_TYPE)
        )

        # Holding Registers: 0..9 legacy test data, 10..19 conveyor speed setpoints.
        hr_initial = (
            [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
            + [0] * MAX_DEVICES_PER_TYPE
        )
        self._hr_block = WriteCallbackDataBlock(
            0, hr_initial, write_callback=self._on_hr_write
        )
        # Input Registers: address 0..9 (read-only test data)
        self._ir_block = ModbusSequentialDataBlock(
            0, [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010]
        )

        # 
        slave_ctx = ModbusDeviceContext(
            di=self._di_block,
            co=self._coil_block,
            hr=self._hr_block,
            ir=self._ir_block,
        )
        self._server_context = ModbusServerContext(
            devices={self._unit_id: slave_ctx}, single=False
        )

        for i, door_id in enumerate(self._door_ids):
            if i >= MAX_DEVICES_PER_TYPE:
                self.get_logger().warn(
                    f'Max {MAX_DEVICES_PER_TYPE} doors supported, skipping {door_id}'
                )
                break

            pub = self.create_publisher(Bool, f'/door/{door_id}/cmd_topic', 10)
            self._door_publishers[i] = pub

            init_door_subscriber(
                node=self,
                device_id=door_id,
                coil_index=i,
                di_block=self._di_block,
            )

            self.get_logger().info(
                f'Door [{door_id}] mapped: coil {i} -> /door/{door_id}/cmd_topic, '
                f'discrete input {i} <- /door/{door_id}/state'
            )

        for i, conv_id in enumerate(self._conveyor_ids):
            if i >= MAX_DEVICES_PER_TYPE:
                self.get_logger().warn(
                    f'Max {MAX_DEVICES_PER_TYPE} conveyors supported, skipping {conv_id}'
                )
                break

            idx = CONVEYOR_BASE + i
            pub = self.create_publisher(Float32, f'/conveyor/{conv_id}/speed_cmd', 10)
            self._conveyor_publishers[idx] = pub

            init_conveyor_subscriber(
                node=self,
                device_id=conv_id,
                di_index=idx,
                di_block=self._di_block,
            )

            self.get_logger().info(
                f'Conveyor [{conv_id}] mapped: coil {idx} (on/off @ {self._conveyor_default_speed:.2f}), '
                f'HR {idx} -> /conveyor/{conv_id}/speed_cmd, '
                f'discrete input {idx} <- /conveyor/{conv_id}/status'
            )

        # Start Modbus TCP server in background thread
        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()

        self.get_logger().info(
            f'Modbus TCP server starting on {self._host}:{self._port} '
            f'(unit_id={self._unit_id})'
        )

    def _run_server(self) -> None:
        StartTcpServer(
            context=self._server_context,
            address=(self._host, self._port),
        )

    def _load_devices(self, override_path: str) -> tuple[list[str], list[str]]:
        """Read devices.yaml and split IDs by type."""
        config_path = override_path or os.path.join(
            get_package_share_directory('syncai_modbus_server'),
            'config',
            'devices.yaml',
        )
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        except Exception as err:
            self.get_logger().warn(
                f'Failed to load device config at {config_path}: {err}'
            )
            return [], []

        door_ids: list[str] = []
        conveyor_ids: list[str] = []
        for device in config.get('devices', []):
            device_id = device.get('id')
            device_type = device.get('type')
            if not device_id or not device_type:
                continue
            if device_type == 'door':
                door_ids.append(device_id)
            elif device_type == 'conveyor':
                conveyor_ids.append(device_id)
            else:
                self.get_logger().warn(
                    f'Unknown device type "{device_type}" for {device_id}, skipping'
                )

        self.get_logger().info(
            f'Loaded device config from {config_path}: '
            f'{len(door_ids)} door(s), {len(conveyor_ids)} conveyor(s)'
        )
        return door_ids, conveyor_ids

    def _on_coil_write(self, address: int, values: list) -> None:
        """Coils 0..9 = door open/close; coils 10..19 = conveyor on/off (fixed speed)."""
        base = address - 1  # pymodbus internal offset
        for offset, val in enumerate(values):
            idx = base + offset
            if idx in self._door_publishers:
                msg = Bool()
                msg.data = bool(val)
                self._door_publishers[idx].publish(msg)
                action = 'OPEN' if val else 'CLOSE'
                self.get_logger().info(
                    f'Coil {idx} written -> {action} door '
                    f'(topic: {self._door_publishers[idx].topic_name})'
                )
            elif idx in self._conveyor_publishers:
                speed = self._conveyor_default_speed if val else 0.0
                msg = Float32()
                msg.data = float(speed)
                self._conveyor_publishers[idx].publish(msg)
                action = 'START' if val else 'STOP'
                self.get_logger().info(
                    f'Coil {idx} written -> {action} conveyor @ {msg.data:.2f} '
                    f'(topic: {self._conveyor_publishers[idx].topic_name})'
                )

    def _on_hr_write(self, address: int, values: list) -> None:
        """Publish conveyor speed when a client writes to a conveyor HR slot."""
        base = address - 1  # pymodbus internal offset
        for offset, raw in enumerate(values):
            idx = base + offset
            if idx not in self._conveyor_publishers:
                continue
            # u16 0..100 -> 0.00..1.00; clamp defensively against out-of-range writes.
            speed = max(0, min(100, int(raw))) / 100.0
            msg = Float32()
            msg.data = float(speed)
            self._conveyor_publishers[idx].publish(msg)
            self.get_logger().info(
                f'HR {idx} written -> speed {msg.data:.2f} '
                f'(topic: {self._conveyor_publishers[idx].topic_name})'
            )


def main(args=None):
    rclpy.init(args=args)
    node = ModbusServerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
