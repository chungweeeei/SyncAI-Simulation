import structlog

import rclpy
from rclpy.node import Node

from syncai_robot_api.repositories.robot.robot import init_robot_repo
from syncai_robot_api.subscribers.robot_state_subscriber import init_robot_state_subscriber

from syncai_robot_api.gateways.agent import init_agent_gateway

from syncai_robot_api.jobs.send_robot_state import init_send_robot_state_job

class SyncAIRobotAPI(Node):

    def __init__(self, logger: structlog.stdlib.BoundLogger):
        super().__init__('syncai_robot_api')

        self._logger = logger
        
        # Register repositories
        robot_repo = init_robot_repo(logger=logger)

        # Register gateways
        agent_gateway = init_agent_gateway(logger=logger)

        init_robot_state_subscriber(logger=logger, node=self, robot_repo=robot_repo)

        # Register jobs
        init_send_robot_state_job(logger=logger, robot_repo=robot_repo, agent_gateway=agent_gateway)

def main():
    rclpy.init()

    logger = structlog.get_logger()
    node = SyncAIRobotAPI(logger=logger)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()