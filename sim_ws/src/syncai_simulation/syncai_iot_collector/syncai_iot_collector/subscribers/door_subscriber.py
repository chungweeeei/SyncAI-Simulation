from rclpy.node import Node
from rclpy.impl.rcutils_logger import RcutilsLogger
from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSHistoryPolicy,
    QoSDurabilityPolicy
)

from std_msgs.msg import String

from syncai_iot_collector.gateways.agent import AgentGateway
from syncai_iot_collector.gateways.agent_schema import EventDetail, EventSeverity, IOTDeviceType

class DoorSubscriber:
    def __init__(self, logger: RcutilsLogger, device_id: str, agent_gateway: AgentGateway) -> None:
        self._device_id = device_id
        self._logger = logger
        self._agent_gateway = agent_gateway

    def register(self, node: Node) -> None:
        topic = f"/door/{self._device_id}/state"
        self._sub = node.create_subscription(
            msg_type=String,
            topic=topic,
            callback=self._door_cb,
            qos_profile=QoSProfile(
                depth=5,
                reliability=QoSReliabilityPolicy.RELIABLE,
                history=QoSHistoryPolicy.KEEP_LAST,
                durability=QoSDurabilityPolicy.VOLATILE
            )
        )
        self._logger.info(f"[DoorSubscriber] Registered subscriber for {topic}")

    def _door_cb(self, msg: String) -> None:
        if msg.data == "open":
            try:
                self._agent_gateway.send_building_event(
                    severity=EventSeverity.LOW,
                    detail=EventDetail(
                        device_type=IOTDeviceType.DOOR,
                        device_id=self._device_id
                    )
                )
            except Exception as err:
                self._logger.warning(f"[DoorSubscriber] Failed to send building event, error={err}")


def init_door_subscriber(node: Node, device_id: str, agent_gateway: AgentGateway) -> None:
    door_subscriber = DoorSubscriber(
        logger=node.get_logger(),
        device_id=device_id,
        agent_gateway=agent_gateway
    )
    door_subscriber.register(node)