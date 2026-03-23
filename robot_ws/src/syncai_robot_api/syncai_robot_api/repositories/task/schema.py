from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


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


class StepParams(BaseModel):
    x: float
    y: float
    r: float


# --- Request models (from external client) ---

class StepRequest(BaseModel):
    id: str
    name: str
    type: str
    params: StepParams


class TaskPayloadRequest(BaseModel):
    steps: List[StepRequest]


class TaskRequest(BaseModel):
    action: str
    id: str
    timestamp: float
    payload: TaskPayloadRequest


# --- Internal models (with status tracking) ---

class Step(BaseModel):
    id: str
    name: str
    type: str
    params: StepParams
    status: StepStatus = StepStatus.PENDING
    error_msg: Optional[str] = None


class TaskPayload(BaseModel):
    steps: List[Step]


class Task(BaseModel):
    action: str
    id: str
    timestamp: float
    payload: TaskPayload
    status: TaskStatus = TaskStatus.PENDING
    current_step_index: int = 0
    error_msg: Optional[str] = None

    @staticmethod
    def from_request(req: 'TaskRequest') -> 'Task':
        steps = [
            Step(id=s.id, name=s.name, type=s.type, params=s.params)
            for s in req.payload.steps
        ]
        return Task(
            action=req.action,
            id=req.id,
            timestamp=req.timestamp,
            payload=TaskPayload(steps=steps),
        )


class TaskResponse(BaseModel):
    id: str
    status: TaskStatus
    message: str
