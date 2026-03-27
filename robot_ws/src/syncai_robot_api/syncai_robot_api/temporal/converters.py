from dataclasses import dataclass, field
from typing import List

from syncai_robot_api.repositories.task.schema import Task


@dataclass
class StepInput:
    task_id: str
    step_index: int
    step_type: str
    params: dict


@dataclass
class StepResult:
    success: bool
    message: str


@dataclass
class TaskWorkflowInput:
    task_id: str
    steps: List[StepInput] = field(default_factory=list)

    @classmethod
    def from_task(cls, task: Task) -> "TaskWorkflowInput":
        steps = []
        for i, step in enumerate(task.payload.steps):
            steps.append(StepInput(
                task_id=task.id,
                step_index=i,
                step_type=step.type.value,
                params=step.params.model_dump(),
            ))
        return cls(task_id=task.id, steps=steps)
