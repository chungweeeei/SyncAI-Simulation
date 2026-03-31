import json
import os

import structlog

from confluent_kafka import Producer
from typing import Optional

from syncai_robot_api.repositories.robot.schema import RobotState
from syncai_robot_api.repositories.task.schema import Task
from syncai_robot_api.gateways.agent_schema import build_external_robot_state


class AgentGateway:

    def __init__(self, logger: structlog.stdlib.BoundLogger):
        self._logger = logger
        self._server_ip = os.getenv("SYNCAI_SERVER_IP", "10.8.101.86")
        self._producer: Optional[Producer] = None

    def _ensure_connected(self) -> bool:
        if self._producer is not None:
            return True

        try:
            self._producer = Producer({
                "bootstrap.servers": f"{self._server_ip}:19092",
                "client.id": "syncai-robot-api",
            })
            self._logger.info("[AgentGateway] Kafka producer created", broker=self._server_ip)
            return True
        except Exception as err:
            self._producer = None
            self._logger.warning("[AgentGateway] Kafka producer creation failed", error=str(err))
            return False

    def _on_delivery(self, err, msg):
        if err is not None:
            self._logger.warning("[AgentGateway] Delivery failed", error=str(err))

    def send_robot_state(self, robot_state: RobotState, active_task: Optional[Task] = None):
        if not self._ensure_connected():
            return

        payload = json.dumps(build_external_robot_state(robot_state, active_task))

        try:
            self._producer.produce(
                topic="robot-state",
                key=robot_state.robot_id,
                value=payload,
                callback=self._on_delivery,
            )
            self._producer.poll(0)
        except Exception as err:
            self._logger.warning("[AgentGateway] Produce failed", error=str(err))
    
    def disconnect(self):
        if self._producer:
            self._producer.flush(timeout=5.0)
            self._producer = None


def init_agent_gateway(logger: structlog.stdlib.BoundLogger) -> AgentGateway:
    return AgentGateway(logger=logger)
