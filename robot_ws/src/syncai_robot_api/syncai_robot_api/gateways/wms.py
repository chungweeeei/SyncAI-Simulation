import os
from typing import Tuple

import requests
import structlog


class WmsGateway:

    def __init__(self, logger: structlog.stdlib.BoundLogger, base_url: str):
        self._logger = logger
        self._base_url = base_url.rstrip("/")

    def occupy_cell(self, cell_id: str, robot_id: str) -> Tuple[bool, str]:
        url = f"{self._base_url}/api/v1/wms/cells/{cell_id}/occupy"
        payload = {"robot_id": robot_id}

        try:
            resp = requests.post(url, json=payload, timeout=5)
        except requests.RequestException as e:
            self._logger.warning(
                "[WmsGateway] occupy_cell request failed",
                cell_id=cell_id, robot_id=robot_id, error=str(e),
            )
            return False, f"WMS request failed: {e}"

        if resp.status_code == 200:
            return True, "Occupancy updated"

        try:
            detail = resp.json().get("detail", resp.text)
        except ValueError:
            detail = resp.text
        self._logger.warning(
            "[WmsGateway] occupy_cell rejected",
            cell_id=cell_id, robot_id=robot_id,
            status=resp.status_code, detail=detail,
        )
        return False, f"HTTP {resp.status_code}: {detail}"

    def release_robot(self, robot_id: str) -> Tuple[bool, str]:
        url = f"{self._base_url}/api/v1/wms/cells/release"
        payload = {"robot_id": robot_id}

        try:
            resp = requests.post(url, json=payload, timeout=5)
        except requests.RequestException as e:
            self._logger.warning(
                "[WmsGateway] release_robot request failed",
                robot_id=robot_id, error=str(e),
            )
            return False, f"WMS request failed: {e}"

        if resp.status_code == 200:
            return True, "Robot released"

        try:
            detail = resp.json().get("detail", resp.text)
        except ValueError:
            detail = resp.text
        self._logger.warning(
            "[WmsGateway] release_robot rejected",
            robot_id=robot_id,
            status=resp.status_code, detail=detail,
        )
        return False, f"HTTP {resp.status_code}: {detail}"


def init_wms_gateway(logger: structlog.stdlib.BoundLogger) -> WmsGateway:
    base_url = os.getenv("SYNCAI_WMS_URL", "http://localhost:8100")
    return WmsGateway(logger=logger, base_url=base_url)
