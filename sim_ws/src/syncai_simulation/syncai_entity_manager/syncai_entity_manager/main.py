import threading

import rclpy
from rclpy.node import Node
import uvicorn

from syncai_entity_manager.gateways.gazebo import GazeboGateway
from syncai_entity_manager.gateways.bridge import BridgeGateway
from syncai_entity_manager.repositories.entity import EntityRepo
from syncai_entity_manager.server import create_app


class EntityManagerNode(Node):

    def __init__(self):
        super().__init__('entity_manager')

        logger = self.get_logger()

        gazebo_gateway = GazeboGateway(logger=logger)
        bridge_gateway = BridgeGateway(logger=logger)
        entity_repo = EntityRepo(logger=logger)

        app = create_app(
            gazebo_gateway=gazebo_gateway,
            bridge_gateway=bridge_gateway,
            entity_repo=entity_repo,
        )

        self._server_thread = threading.Thread(
            target=self._run_server, args=(app, "0.0.0.0", 3000), daemon=True
        )
        self._server_thread.start()

    def _run_server(self, app, host: str, port: int) -> None:
        config = uvicorn.Config(app, host=host, port=port, log_level='warning')
        server = uvicorn.Server(config)
        server.run()


def main(args=None):
    rclpy.init(args=args)
    node = EntityManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
