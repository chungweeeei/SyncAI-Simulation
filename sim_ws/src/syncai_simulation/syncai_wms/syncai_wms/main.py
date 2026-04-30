import structlog

import rclpy
from rclpy.node import Node

from syncai_wms import logger as _logger_config  # noqa: F401  (configures structlog)
from syncai_wms.gateways.spawn import init_spawn_gateway
from syncai_wms.repositories.pending_cargo import init_pending_cargo_repo
from syncai_wms.server import start_api_server
from syncai_wms.subscribers.cargo_pending_subscriber import (
    init_cargo_pending_subscriber,
)


class SyncAIWMS(Node):

    def __init__(self, logger: structlog.stdlib.BoundLogger):
        super().__init__("syncai_wms")
        self._log = logger

        pending_repo = init_pending_cargo_repo(logger=logger)
        spawn_gateway = init_spawn_gateway(logger=logger, node=self)

        init_cargo_pending_subscriber(logger=logger, node=self, repo=pending_repo)

        start_api_server(
            logger=logger,
            spawn_gateway=spawn_gateway,
            pending_repo=pending_repo,
        )


def main() -> None:
    rclpy.init()

    logger = structlog.get_logger()
    node = SyncAIWMS(logger=logger)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
