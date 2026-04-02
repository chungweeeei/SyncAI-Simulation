import os
from typing import Tuple

import requests
import structlog


class EntityGateway:

    def __init__(self, logger: structlog.stdlib.BoundLogger, base_url: str):
        self._logger = logger
        self._base_url = base_url.rstrip("/")

    def spawn_vertex(self, name: str, x: float, y: float, yaw: float) -> Tuple[bool, str]:
        url = f"{self._base_url}/api/v1/entities/"
        payload = {
            "model_type": "vertex",
            "entity_name": name,
            "pose": {"x": x, "y": y, "z": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": yaw},
        }

        self._logger.info("[EntityGateway] Spawning vertex", name=name, x=x, y=y, yaw=yaw)

        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
        except requests.RequestException as e:
            self._logger.error("[EntityGateway] spawn_vertex failed", error=str(e))
            return False, f"Entity manager request failed: {e}"

        if resp.status_code == 201:
            return True, data.get("message", "Vertex spawned")

        return False, data.get("detail", data.get("message", f"HTTP {resp.status_code}"))

    def delete_vertex(self, name: str) -> Tuple[bool, str]:
        url = f"{self._base_url}/api/v1/entities/{name}"

        self._logger.info("[EntityGateway] Deleting vertex", name=name)

        try:
            resp = requests.delete(url, timeout=10)
            data = resp.json()
        except requests.RequestException as e:
            self._logger.error("[EntityGateway] delete_vertex failed", error=str(e))
            return False, f"Entity manager request failed: {e}"

        if resp.status_code == 200:
            return True, data.get("message", "Vertex deleted")

        return False, data.get("detail", data.get("message", f"HTTP {resp.status_code}"))


def init_entity_gateway(logger: structlog.stdlib.BoundLogger) -> EntityGateway:
    base_url = os.getenv("SYNCAI_ENTITY_MANAGER_URL", "http://syncai-simulation:3000")
    return EntityGateway(logger=logger, base_url=base_url)
