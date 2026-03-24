import structlog
import threading

from typing import Optional

from syncai_robot_api.repositories.robot.schema import RobotState


class RobotRepo:

    def __init__(self, logger: structlog.BoundLogger):
        self._logger = logger
        
        # In-Process memory cache for robot state
        self._robot_state_lock = threading.Lock()
        self._robot_state: Optional[RobotState] = None

    def update_robot_state(self, state: RobotState):
        with self._robot_state_lock:
            self._robot_state = state

    def get_robot_state(self) -> Optional[RobotState]:
        with self._robot_state_lock:
            return self._robot_state

def init_robot_repo(logger: structlog.stdlib.BoundLogger) -> RobotRepo:
    return RobotRepo(logger=logger)