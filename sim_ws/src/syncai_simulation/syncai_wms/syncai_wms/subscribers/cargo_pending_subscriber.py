import json

import structlog
from rclpy.node import Node
from std_msgs.msg import String

from syncai_wms.repositories.pending_cargo import PendingCargoRepo


class CargoPendingSubscriber:

    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger,
        node: Node,
        repo: PendingCargoRepo,
    ):
        self._logger = logger
        self._repo = repo
        self._sub = node.create_subscription(
            String,
            "/cargo/pending",
            self._callback,
            10,
        )

    def _callback(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as e:
            self._logger.warning(
                "[CargoPendingSubscriber] invalid JSON", data=msg.data, error=str(e)
            )
            return

        # Accept either {"pending": [...], "stamp_sec": ...} or a bare list.
        if isinstance(payload, dict):
            items = payload.get("pending", [])
            stamp_sec = payload.get("stamp_sec")
        elif isinstance(payload, list):
            items = payload
            stamp_sec = None
        else:
            self._logger.warning(
                "[CargoPendingSubscriber] unexpected payload shape", data=msg.data
            )
            return

        if not isinstance(items, list):
            self._logger.warning(
                "[CargoPendingSubscriber] 'pending' is not a list", data=msg.data
            )
            return

        self._repo.update(items, stamp_sec)


def init_cargo_pending_subscriber(
    logger: structlog.stdlib.BoundLogger,
    node: Node,
    repo: PendingCargoRepo,
) -> CargoPendingSubscriber:
    return CargoPendingSubscriber(logger=logger, node=node, repo=repo)
