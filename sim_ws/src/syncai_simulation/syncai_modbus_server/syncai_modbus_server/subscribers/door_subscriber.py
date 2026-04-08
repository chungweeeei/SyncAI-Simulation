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


class DoorStateSubscriber:

    def __init__(
        self,
        logger: RcutilsLogger,
        device_id: str,
        coil_index: int,
        di_block: ModbusSequentialDataBlock,
    ) -> None:
        self._device_id = device_id
        self._coil_index = coil_index
        self._logger = logger
        self._di_block = di_block

    def register(self, node: Node) -> None:
        topic = f"/door/{self._device_id}/state"
        self._sub = node.create_subscription(
            msg_type=String,
            topic=topic,
            callback=self._state_cb,
            qos_profile=QoSProfile(
                depth=5,
                reliability=QoSReliabilityPolicy.RELIABLE,
                history=QoSHistoryPolicy.KEEP_LAST,
                durability=QoSDurabilityPolicy.VOLATILE,
            ),
        )
        self._logger.info(f"[DoorStateSubscriber] Registered subscriber for {topic}")

    def _state_cb(self, msg: String) -> None:
        state = msg.data.lower()
        is_open = state in ("open", "opening")
        # +1 for pymodbus internal offset
        self._di_block.setValues(self._coil_index + 1, [is_open])
        self._logger.debug(
            f"[DoorStateSubscriber] Door {self._device_id} state: {state} "
            f"-> DI[{self._coil_index}] = {is_open}"
        )


def init_door_subscriber(
    node: Node,
    device_id: str,
    coil_index: int,
    di_block: ModbusSequentialDataBlock,
) -> None:
    subscriber = DoorStateSubscriber(
        logger=node.get_logger(),
        device_id=device_id,
        coil_index=coil_index,
        di_block=di_block,
    )
    subscriber.register(node)
