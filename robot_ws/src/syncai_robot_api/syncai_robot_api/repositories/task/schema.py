from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

class TaskActionType(str, Enum):
    COMMAND = "COMMAND"
    TASK = "TASK"

class StepType(str, Enum):
    MOVE = "MOVE"
    WAIT = "WAIT"
    DOOR = "DOOR"
    CHARGE = "CHARGE"

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class StepStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class MoveParams(BaseModel):
    x: float = Field(..., description="X coordinate for movement", example=0.0)
    y: float = Field(..., description="Y coordinate for movement", example=0.0)
    r: float = Field(..., description="Rotation in degrees", example=0.0)

class WaitParams(BaseModel):
    durationSec: float = Field(..., description="Duration to wait in seconds", example=5.0)

class DoorParams(BaseModel):
    open: bool = Field(..., description="Whether to open (true) or close (false) the door", example=True)

class ChargeParams(BaseModel):
    x: float = Field(..., description="X coordinate near charging station", example=-2.0)
    y: float = Field(..., description="Y coordinate near charging station", example=5.0)
    r: float = Field(0.0, description="Rotation in degrees", example=0.0)

# --- Internal models (with status tracking) ---
class Step(BaseModel):
    id: str
    name: str
    type: StepType
    params: MoveParams | WaitParams | DoorParams | ChargeParams
    status: StepStatus = StepStatus.PENDING
    error_msg: Optional[str] = None


class TaskPayload(BaseModel):
    steps: List[Step]


class Task(BaseModel):
    action: TaskActionType
    id: str
    timestamp: float
    payload: TaskPayload
    status: TaskStatus = TaskStatus.PENDING
    current_step_index: int = 0
    error_msg: Optional[str] = None
    workflow_id: Optional[str] = None
