import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartTcpServer

from syncai_modbus_server.datablock import CoilWriteDataBlock
from syncai_modbus_server.subscribers.door_subscriber import init_door_subscriber


class ModbusServerNode(Node):

    def __init__(self):
        super().__init__('modbus_server')

        self.declare_parameter('host', '127.0.0.1')
        self.declare_parameter('port', 5020)
        self.declare_parameter('unit_id', 1)
        self.declare_parameter('door_ids', ['door_01'])

        self._host = self.get_parameter('host').value
        self._port = self.get_parameter('port').value
        self._unit_id = self.get_parameter('unit_id').value
        self._door_ids = self.get_parameter('door_ids').value

        # Door publishers: coil address -> publisher
        self._door_publishers: dict[int, object] = {}

        # Coils: address 0..9 (one per door, rest reserved)
        # CoilWriteDataBlock allows read and write
        self._coil_block = CoilWriteDataBlock(
            0, [False] * 10, write_callback=self._on_coil_write
        )

        # Discrete Inputs: address 0..9 (door states)
        # Discrete inputs are read-only, updated by ROS subscribers
        self._di_block = ModbusSequentialDataBlock(0, [False] * 10)

        # Holding Registers: address 0..9 (test data)
        self._hr_block = ModbusSequentialDataBlock(
            0, [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
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
            if i >= 10:
                self.get_logger().warn(f'Max 10 doors supported, skipping {door_id}')
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

    def _on_coil_write(self, address: int, values: list) -> None:
        """Called when a Modbus client writes to coils."""
        for offset, val in enumerate(values):
            coil_addr = address - 1  # pymodbus internal offset
            idx = coil_addr + offset
            if idx in self._door_publishers:
                msg = Bool()
                msg.data = bool(val)
                self._door_publishers[idx].publish(msg)
                action = 'OPEN' if val else 'CLOSE'
                self.get_logger().info(
                    f'Coil {idx} written -> {action} door '
                    f'(topic: {self._door_publishers[idx].topic_name})'
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
