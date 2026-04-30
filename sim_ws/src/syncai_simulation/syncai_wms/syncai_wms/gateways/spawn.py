from typing import Tuple

import structlog
from rclpy.node import Node
from std_msgs.msg import String


class SpawnGateway:

    def __init__(self, logger: structlog.stdlib.BoundLogger, node: Node):
        self._logger = logger
        self._node = node
        self._pubs: dict[str, object] = {}

    def spawn(self, conveyor_id: str, box_id: str) -> Tuple[bool, str]:
        pub = self._pubs.get(conveyor_id)
        if pub is None:
            pub = self._node.create_publisher(
                String, f"/cargo/{conveyor_id}/spawn_cmd", 10
            )
            self._pubs[conveyor_id] = pub

        msg = String()
        msg.data = box_id
        pub.publish(msg)
        self._logger.info(
            "[SpawnGateway] spawn", conveyor=conveyor_id, box=box_id
        )
        return True, f"spawn published to /cargo/{conveyor_id}/spawn_cmd ({box_id})"


def init_spawn_gateway(
    logger: structlog.stdlib.BoundLogger, node: Node
) -> SpawnGateway:
    return SpawnGateway(logger=logger, node=node)
