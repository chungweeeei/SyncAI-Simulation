from typing import List

from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, status

from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.repositories.task.schema import (
    TaskActionType,
    StepType,
    MoveParams,
    WaitParams,
    Task, 
    TaskPayload, 
    Step,
    TaskStatus
)
from syncai_robot_api.gateways.navigation import NavigationGateway

# --- Request models (from external client) ---

class StepRequest(BaseModel):
    id: str = Field(..., description="Unique identifier of the step", example="step1")
    name: str = Field(..., description="Name of the step", example="Move to point")
    type: StepType = Field(..., description="Type of the step", example="MOVE")
    params: MoveParams | WaitParams = Field(..., description="Parameters for the step")

class TaskPayloadRequest(BaseModel):
    steps: List[StepRequest]

class TaskRequest(BaseModel):
    action: TaskActionType = Field(..., description="Type of the task action", example="TASK")
    id: str = Field(..., description="Unique identifier of the task", example="task123")
    timestamp: float = Field(..., description="Timestamp of the task creation")
    payload: TaskPayloadRequest = Field(..., description="Payload containing the task steps")


class TaskResponse(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier of the task",
        example="task123"
    ),
    status: TaskStatus = Field(
        ...,
        description="Current status of the task",
        example="PENDING"
    )
    message: str = Field(
        ...,
        description="Additional message or error information",
        example="Task created successfully"
    )


def init_task_router(task_repo: TaskRepo, nav_gateway: NavigationGateway) -> APIRouter:

    router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

    @router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
    async def create_task(req: TaskRequest):
        # Step1: Validate and convert request to internal Task model
        task = Task(
            action=req.action,
            id=req.id,
            timestamp=req.timestamp,
            payload=TaskPayload(
                steps=[
                    Step(
                        id=s.id,
                        name=s.name,
                        type=s.type,
                        params=s.params
                    ) for s in req.payload.steps
                ]
            )
        )
        
        # Step2: Start add task to repository
        success = task_repo.add_task(task)
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task {task.id} already exists")

        return TaskResponse(id=task.id, status=TaskStatus.PENDING, message="Task created successfully")

    @router.get("/", response_model=List[Task])
    async def get_all_tasks():
        return task_repo.get_all_tasks()

    @router.get("/{task_id}", response_model=Task)
    async def get_task(task_id: str):
        task = task_repo.get_task(task_id=task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")
        return task
    
    @router.delete("/{task_id}", response_model=TaskResponse)
    async def cancel_task(task_id: str):

        task = task_repo.get_task(task_id=task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")

        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task is already {task.status}")

        task_repo.update_task_status(task_id, TaskStatus.CANCELLED)
        nav_gateway.cancel_current_goal()

        return TaskResponse(id=task_id, status=TaskStatus.CANCELLED, message="Task cancel requested")


    return router