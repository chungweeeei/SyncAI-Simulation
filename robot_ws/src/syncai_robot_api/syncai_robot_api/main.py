import os
import configparser

import structlog

import rclpy
from rclpy.node import Node

from syncai_robot_api.repositories.robot.robot import init_robot_repo
from syncai_robot_api.repositories.task.task import init_task_repo
from syncai_robot_api.subscribers.robot_state_subscriber import init_robot_state_subscriber

from syncai_robot_api.gateways.agent import init_agent_gateway
from syncai_robot_api.gateways.navigation import init_navigation_gateway

from syncai_robot_api.jobs.send_robot_state import init_send_robot_state_job
from syncai_robot_api.jobs.task_executor import init_task_executor_job

from syncai_robot_api.server import start_api_server


def _read_robot_id():
    data_dir = os.path.expanduser("~/data")
    config = configparser.ConfigParser()
    config.read(os.path.join(data_dir, "system.ini"))
    return config.get("identity", "robot_id", fallback="robot01")


class SyncAIRobotAPI(Node):

    def __init__(self, logger: structlog.stdlib.BoundLogger):
        super().__init__('syncai_robot_api')

        self._log = logger

        robot_id = _read_robot_id()
        self._log.info("[SyncAIRobotAPI] Initialized", robot_id=robot_id)

        # Register repositories
        robot_repo = init_robot_repo(logger=logger)
        task_repo = init_task_repo(logger=logger)

        # Register gateways
        agent_gateway = init_agent_gateway(logger=logger)
        nav_gateway = init_navigation_gateway(logger=logger, node=self, robot_id=robot_id)

        # Register subscribers
        init_robot_state_subscriber(logger=logger, node=self, robot_repo=robot_repo)

        # Register jobs
        init_send_robot_state_job(logger=logger, robot_repo=robot_repo, agent_gateway=agent_gateway)
        init_task_executor_job(logger=logger, task_repo=task_repo, nav_gateway=nav_gateway)

        # Start HTTP API server
        start_api_server(logger=logger, task_repo=task_repo, nav_gateway=nav_gateway)


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
