import os
import configparser

import structlog
from dataclasses import dataclass

import rclpy
from rclpy.node import Node

from syncai_robot_api.repositories.robot.robot import init_robot_repo
from syncai_robot_api.repositories.task.task import init_task_repo
from syncai_robot_api.subscribers.robot_state_subscriber import init_robot_state_subscriber

from syncai_robot_api.gateways.agent import init_agent_gateway
from syncai_robot_api.gateways.robot import init_robot_gateway
from syncai_robot_api.gateways.modbus import ModbusGateway
from syncai_robot_api.gateways.entity import init_entity_gateway

from syncai_robot_api.jobs.send_robot_state import init_send_robot_state_job
from syncai_robot_api.temporal.worker import start_temporal_worker

from syncai_robot_api.server import start_api_server

@dataclass
class RobotConfig:
    robot_id: str
    map: str

def _read_robot_config() -> RobotConfig:
    data_dir = os.path.expanduser("~/data")
    config = configparser.ConfigParser()
    config.read(os.path.join(data_dir, "system.ini"))
    robot_id = config.get("identity", "robot_id", fallback="robot01")
    map_name = config.get("spawn", "map", fallback="default")
    return RobotConfig(robot_id=robot_id, map=map_name)


class SyncAIRobotAPI(Node):

    def __init__(self, logger: structlog.stdlib.BoundLogger):
        super().__init__('syncai_robot_api')

        self._log = logger

        robot_config = _read_robot_config()

        # Register repositories
        robot_repo = init_robot_repo(logger=logger)
        task_repo = init_task_repo(logger=logger)

        # Register gateways
        # agent_gateway = init_agent_gateway(logger=logger)
        robot_gateway = init_robot_gateway(logger=logger, node=self, robot_id=robot_config.robot_id)
        modbus_gateway = ModbusGateway(logger=logger)
        entity_gateway = init_entity_gateway(logger=logger)

        # Register subscribers
        init_robot_state_subscriber(logger=logger, node=self, robot_repo=robot_repo)
        # Register jobs
        # init_send_robot_state_job(logger=logger, robot_repo=robot_repo, task_repo=task_repo, agent_gateway=agent_gateway)

        # Start Temporal Worker (replaces TaskExecutorJob)
        start_temporal_worker(logger=logger, robot_gateway=robot_gateway, modbus_gateway=modbus_gateway, task_repo=task_repo, robot_id=robot_config.robot_id)

        # Start HTTP API server
        start_api_server(
            logger=logger,
            robot_repo=robot_repo,
            task_repo=task_repo,
            robot_gateway=robot_gateway,
            entity_gateway=entity_gateway,
            robot_id=robot_config.robot_id,
            map_name=robot_config.map,
        )


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
