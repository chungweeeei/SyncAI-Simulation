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


PHASE_IDLE = 0
PHASE_RUNNING = 1
PHASE_HANDOFF = 2
PHASE_CARRIED = 3
PHASE_DROPPED = 4

_PHASE_BY_PREFIX = {
    "stopped": PHASE_IDLE,
    "limit_triggered": PHASE_IDLE,
    "running": PHASE_RUNNING,
    "belt": PHASE_RUNNING,
    "handoff": PHASE_HANDOFF,
    "carried": PHASE_CARRIED,
    "dropped": PHASE_DROPPED,
}


def _phase_from_status(data: str) -> int | None:
    """Map /conveyor/<id>/status string to phase enum.

    Returns None for transient *_rejected sentinels so the previous phase
    stays latched (the conveyor reverts within one tick anyway).
    """
    prefix = (data or "").strip().lower().split(":", 1)[0]
    if not prefix:
        return PHASE_IDLE
    if prefix.endswith("_rejected"):
        return None
    return _PHASE_BY_PREFIX.get(prefix, PHASE_IDLE)


class ConveyorStatusSubscriber:

    def __init__(
        self,
        logger: RcutilsLogger,
        device_id: str,
        di_index: int,
        di_block: ModbusSequentialDataBlock,
        ir_index: int,
        ir_block: ModbusSequentialDataBlock,
    ) -> None:
        self._device_id = device_id
        self._di_index = di_index
        self._logger = logger
        self._di_block = di_block
        self._ir_index = ir_index
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
        state = msg.data.strip().lower()
        is_running = state == "running"
        # +1 for pymodbus internal offset
        self._di_block.setValues(self._di_index + 1, [is_running])

        phase = _phase_from_status(msg.data)
        if phase is not None:
            self._ir_block.setValues(self._ir_index + 1, [phase])
        self._logger.debug(
            f"[ConveyorStatusSubscriber] Conveyor {self._device_id} state: {state} "
            f"-> DI[{self._di_index}] = {is_running}, IR[{self._ir_index}] = {phase}"
        )


def init_conveyor_subscriber(
    node: Node,
    device_id: str,
    di_index: int,
    di_block: ModbusSequentialDataBlock,
    ir_index: int,
    ir_block: ModbusSequentialDataBlock,
) -> None:
    subscriber = ConveyorStatusSubscriber(
        logger=node.get_logger(),
        device_id=device_id,
        di_index=di_index,
        di_block=di_block,
        ir_index=ir_index,
        ir_block=ir_block,
    )
    subscriber.register(node)
