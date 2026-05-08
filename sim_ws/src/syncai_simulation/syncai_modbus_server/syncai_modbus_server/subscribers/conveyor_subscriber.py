from rclpy.node import Node
from rclpy.impl.rcutils_logger import RcutilsLogger
from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSHistoryPolicy,
    QoSDurabilityPolicy,
)

from std_msgs.msg import String

from pymodbus.datastore import ModbusSequentialDataBlock


class ConveyorStatusSubscriber:

    def __init__(
        self,
        logger: RcutilsLogger,
        device_id: str,
        di_index: int,
        di_block: ModbusSequentialDataBlock,
        ir_index: int,
        ir_width: int,
        ir_block: ModbusSequentialDataBlock,
    ) -> None:
        self._device_id = device_id
        self._di_index = di_index
        self._logger = logger
        self._di_block = di_block
        self._ir_index = ir_index
        self._ir_width = ir_width
        self._ir_block = ir_block

    def register(self, node: Node) -> None:
        topic = f"/conveyor/{self._device_id}/status"
        self._sub = node.create_subscription(
            msg_type=String,
            topic=topic,
            callback=self._status_cb,
            qos_profile=QoSProfile(
                depth=5,
                reliability=QoSReliabilityPolicy.RELIABLE,
                history=QoSHistoryPolicy.KEEP_LAST,
                durability=QoSDurabilityPolicy.VOLATILE,
            ),
        )
        self._logger.info(f"[ConveyorStatusSubscriber] Registered subscriber for {topic}")

    def _status_cb(self, msg: String) -> None:
        state = msg.data.strip()
        lower = state.lower()

        if lower.startswith("handoff:"):
            box_id = state.split(":", 1)[1].strip()
            self._write_box_id(box_id)
            is_running = True
        elif lower == "running":
            self._write_box_id("")
            is_running = True
        elif lower == "stopped":
            self._write_box_id("")
            is_running = False
        else:
            self._logger.debug(
                f"[ConveyorStatusSubscriber] {self._device_id} unhandled state: {state}"
            )
            return

        # +1 for pymodbus internal offset
        self._di_block.setValues(self._di_index + 1, [is_running])
        self._logger.debug(
            f"[ConveyorStatusSubscriber] {self._device_id} state: {state} "
            f"-> DI[{self._di_index}]={is_running}"
        )

    def _write_box_id(self, box_id: str) -> None:
        max_bytes = self._ir_width * 2
        encoded = box_id.encode("ascii", errors="replace")[:max_bytes]
        encoded = encoded.ljust(max_bytes, b"\x00")
        words = [
            (encoded[i] << 8) | encoded[i + 1]
            for i in range(0, max_bytes, 2)
        ]
        # +1 for pymodbus internal offset
        self._ir_block.setValues(self._ir_index + 1, words)


def init_conveyor_subscriber(
    node: Node,
    device_id: str,
    di_index: int,
    di_block: ModbusSequentialDataBlock,
    ir_index: int,
    ir_width: int,
    ir_block: ModbusSequentialDataBlock,
) -> None:
    subscriber = ConveyorStatusSubscriber(
        logger=node.get_logger(),
        device_id=device_id,
        di_index=di_index,
        di_block=di_block,
        ir_index=ir_index,
        ir_width=ir_width,
        ir_block=ir_block,
    )
    subscriber.register(node)
