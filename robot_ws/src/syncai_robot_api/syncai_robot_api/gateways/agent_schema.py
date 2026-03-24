import time
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from syncai_robot_api.repositories.robot.schema import RobotState
from syncai_robot_api.repositories.task.schema import Task, StepStatus


class OperatingMode(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    MAINTENANCE = "MAINTENANCE"


class ActionStatus(str, Enum):
    WAITING = "WAITING"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class AgvPosition(BaseModel):
    x: float
    y: float
    theta: float
    mapId: str
    positionInitialized: bool = True


class Velocity(BaseModel):
    vx: float = 0.0
    omega: float = 0.0


class BatteryState(BaseModel):
    batteryCharge: float
    charging: bool = False
    batteryVoltage: float


class ActionStateItem(BaseModel):
    actionId: str
    actionStatus: ActionStatus


class Vda5050State(BaseModel):
    timestamp: int
    version: str = "2.0.0"
    manufacturer: str
    serialNumber: str
    agvPosition: AgvPosition
    velocity: Velocity
    batteryState: BatteryState
    actionState: List[ActionStateItem]
    operatingMode: OperatingMode = OperatingMode.AUTO
    paused: bool = False


_STEP_STATUS_MAP = {
    StepStatus.PENDING: ActionStatus.WAITING,
    StepStatus.IN_PROGRESS: ActionStatus.RUNNING,
    StepStatus.COMPLETED: ActionStatus.FINISHED,
    StepStatus.FAILED: ActionStatus.FAILED,
    StepStatus.CANCELLED: ActionStatus.FAILED,
}


def build_external_robot_state(robot_state: RobotState, active_task: Optional[Task] = None) -> dict:
    timestamp = int(time.time())

    action_state = []
    if active_task is not None:
        idx = active_task.current_step_index
        if idx < len(active_task.payload.steps):
            step = active_task.payload.steps[idx]
            action_state.append(ActionStateItem(
                actionId=step.id,
                actionStatus=_STEP_STATUS_MAP.get(step.status, ActionStatus.WAITING),
            ))

    state = Vda5050State(
        timestamp=timestamp,
        manufacturer="SyncRobotic",
        serialNumber=robot_state.robot_id,
        agvPosition=AgvPosition(
            x=robot_state.pose.x,
            y=robot_state.pose.y,
            theta=robot_state.pose.yaw,
            mapId=robot_state.map,
        ),
        velocity=Velocity(
            vx=robot_state.velocity.vx,
            omega=robot_state.velocity.omega,
        ),
        batteryState=BatteryState(
            batteryCharge=robot_state.battery.percentage,
            batteryVoltage=robot_state.battery.voltage,
        ),
        actionState=action_state,
    )

    return state.model_dump()
