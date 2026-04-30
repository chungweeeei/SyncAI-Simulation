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
    ) -> None:
        self._device_id = device_id
        self._di_index = di_index
        self._logger = logger
        self._di_block = di_block

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
        state = msg.data.strip().lower()
        is_running = state == "running"
        # +1 for pymodbus internal offset
        self._di_block.setValues(self._di_index + 1, [is_running])
        self._logger.debug(
            f"[ConveyorStatusSubscriber] Conveyor {self._device_id} state: {state} "
            f"-> DI[{self._di_index}] = {is_running}"
        )


def init_conveyor_subscriber(
    node: Node,
    device_id: str,
    di_index: int,
    di_block: ModbusSequentialDataBlock,
) -> None:
    subscriber = ConveyorStatusSubscriber(
        logger=node.get_logger(),
        device_id=device_id,
        di_index=di_index,
        di_block=di_block,
    )
    subscriber.register(node)
