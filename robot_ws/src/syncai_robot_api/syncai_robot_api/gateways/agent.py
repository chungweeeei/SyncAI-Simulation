import os
import structlog

from typing import Optional

from websockets.client import connect, WebSocketClientProtocol

from syncai_robot_api.repositories.robot.schema import RobotState

class AgentGateway:

    def __init__(self, logger: structlog.stdlib.BoundLogger, reconnect_interval: float = 5.0):
        self._logger = logger
        self._ws_url = f"ws://{os.getenv("AGENT_HOST", "127.0.0.1")}:{os.getenv("AGENT_PORT", "9090")}"
        
        self._reconnect_interval = reconnect_interval
        self._ws: Optional[WebSocketClientProtocol] = None
        self._connected = False

    def send_robot_state(self, robot_state: RobotState):

        self._logger.info("[AgentGateway][send_robot_state] Sending robot state to agent", robot_state=robot_state)


def init_agent_gateway(logger: structlog.stdlib.BoundLogger) -> AgentGateway:
    agent_gateway = AgentGateway(logger=logger)
    return agent_gateway