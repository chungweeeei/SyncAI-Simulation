import json
import os

import structlog
import yaml
import requests

from confluent_kafka import Producer
from pathlib import Path
from typing import Optional

from syncai_robot_api.repositories.robot.schema import RobotState
from syncai_robot_api.repositories.task.schema import Task
from syncai_robot_api.gateways.agent_schema import build_external_robot_state

from syncai_robot_api.helpers.map_helper import read_pgm_size

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
                "bootstrap.servers": f"{self._server_ip}:9092",
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

    def send_map_info(self, map: str):

        map_yaml = os.path.expanduser(f"~/map/{map}.yaml")
        if not os.path.exists(map_yaml):
            self._logger.error(f"[AgentGateway] {map} map YAML not found" )
            return

        try:
            with open(map_yaml) as f:
                map_config = yaml.load(f, Loader=yaml.CLoader)

            # Read PGM dimensions
            pgm_path = Path(map_yaml).parent / map_config["image"]
            width, height = read_pgm_size(pgm_path)
        except Exception:
            self._logger.error(f"[AgentGateway] Failed to read {map} yaml")
            return

        origin = map_config.get("origin", [0.0, 0.0, 0.0])
        map_id = Path(map_yaml).stem

        # Load vertexes
        vertexes_path = Path(map_yaml).parent / f"{map_id}_vertexes.json"
        vertexes = []
        if vertexes_path.exists():
            with open(vertexes_path) as f:
                vertexes = json.load(f)

        payload = {
            "map_metadata": {
                "map_id": map_id,
                "origin": {"x": origin[0], "y": origin[1], "theta": origin[2]},
                "resolution": map_config.get("resolution", 0.05),
                "width": width,
                "height": height,
            },
            "vertexes": vertexes,
        }

        url = f"http://{self._server_ip}:8000/api/v1/map"
        try:
            resp = requests.post(url, json=payload, timeout=5.0)
            resp.raise_for_status()
            self._logger.info("[AgentGateway] Map info sent", url=url, status=resp.status_code)
        except Exception as err:
            self._logger.warning("[AgentGateway] Failed to send map info", url=url, error=str(err))

    def disconnect(self):
        if self._producer:
            self._producer.flush(timeout=5.0)
            self._producer = None


def init_agent_gateway(logger: structlog.stdlib.BoundLogger) -> AgentGateway:
    return AgentGateway(logger=logger)
