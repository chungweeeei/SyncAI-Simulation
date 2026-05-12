from typing import Tuple

import structlog
from rclpy.node import Node
from std_msgs.msg import String


class CargoGateway:

    def __init__(self, logger: structlog.stdlib.BoundLogger, node: Node, robot_name: str):
        self._logger = logger
        self._node = node
        self._robot_name = robot_name
        self._drop_pub = node.create_publisher(String, "/cargo/drop_cmd", 10)
        self._pickup_pubs: dict[str, object] = {}
        self._carried_box: str | None = None
        self._carried_conveyor: str | None = None

    def pickup(self, conveyor_id: str, box_id: str) -> Tuple[bool, str]:
        pub = self._pickup_pubs.get(conveyor_id)
        if pub is None:
            pub = self._node.create_publisher(
                String, f"/cargo/{conveyor_id}/pickup_cmd", 10
            )
            self._pickup_pubs[conveyor_id] = pub

        payload = f"{box_id}:{self._robot_name}"
        msg = String()
        msg.data = payload
        pub.publish(msg)
        self._logger.info(
            "[CargoGateway] pickup", conveyor=conveyor_id, box=box_id, robot=self._robot_name
        )
        return True, f"pickup published to /cargo/{conveyor_id}/pickup_cmd ({payload})"

    def mark_carried(self, box_id: str, conveyor_id: str) -> None:
        self._carried_box = box_id
        self._carried_conveyor = conveyor_id

    def clear_carried(self) -> None:
        self._carried_box = None
        self._carried_conveyor = None

    def dropoff(self, zone_id: str) -> Tuple[bool, str, str]:
        if self._carried_box is None or self._carried_conveyor is None:
            self._logger.warning("[CargoGateway] dropoff with no carried box", zone=zone_id)
            return False, "dropoff failed: no box currently carried", ""

        box_id = self._carried_box
        conveyor_id = self._carried_conveyor
        payload = f"{box_id}:{zone_id}"
        msg = String()
        msg.data = payload
        self._drop_pub.publish(msg)
        self._logger.info(
            "[CargoGateway] dropoff", box=box_id, zone=zone_id, conveyor=conveyor_id
        )
        return True, f"drop published to /cargo/drop_cmd ({payload})", conveyor_id


def init_cargo_gateway(
    logger: structlog.stdlib.BoundLogger, node: Node, robot_name: str
) -> CargoGateway:
    return CargoGateway(logger=logger, node=node, robot_name=robot_name)
