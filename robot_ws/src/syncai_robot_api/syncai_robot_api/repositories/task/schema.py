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
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"

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
    x: float = Field(..., description="X coordinate for movement", examples=[0.0])
    y: float = Field(..., description="Y coordinate for movement", examples=[0.0])
    r: float = Field(..., description="Rotation in degrees", examples=[0.0])
    cell_id: Optional[str] = Field(
        default=None,
        description="WMS Cell uuid; if provided, robot will report occupancy to WMS on arrival",
        examples=["4386af1d-ffb9-42bc-89f5-9ccd41f887ed"],
    )

class WaitParams(BaseModel):
    durationSec: float = Field(..., description="Duration to wait in seconds", examples=[5.0])

class DoorParams(BaseModel):
    open: bool = Field(..., description="Whether to open (true) or close (false) the door", examples=[True])

class ChargeParams(BaseModel):
    x: float = Field(..., description="X coordinate near charging station", examples=[-2.0])
    y: float = Field(..., description="Y coordinate near charging station", examples=[5.0])
    r: float = Field(0.0, description="Rotation in degrees", examples=[0.0])

class PickupParams(BaseModel):
    conveyor_id: str = Field(..., description="Conveyor device id", examples=["conveyor_01"])

class DropoffParams(BaseModel):
    zone_id: str = Field(..., description="Dropoff zone id", examples=["dropoff_a"])

# --- Internal models (with status tracking) ---
class Step(BaseModel):
    id: str
    name: str
    type: StepType
    params: MoveParams | WaitParams | DoorParams | ChargeParams | PickupParams | DropoffParams
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
    completed_at: Optional[float] = None
