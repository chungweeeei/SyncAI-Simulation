from typing import List

from fastapi import APIRouter, HTTPException

from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.repositories.task.schema import Task, TaskRequest, TaskResponse, TaskStatus
from syncai_robot_api.gateways.navigation import NavigationGateway

router = APIRouter(prefix="/tasks", tags=["tasks"])

_task_repo: TaskRepo = None
_nav_gateway: NavigationGateway = None


def configure(task_repo: TaskRepo, nav_gateway: NavigationGateway):
    global _task_repo, _nav_gateway
    _task_repo = task_repo
    _nav_gateway = nav_gateway


@router.post("/", response_model=TaskResponse)
async def create_task(req: TaskRequest):
    if _task_repo is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    task = Task.from_request(req)
    success = _task_repo.add_task(task)
    if not success:
        raise HTTPException(status_code=409, detail=f"Task {task.id} already exists")

    return TaskResponse(id=task.id, status=task.status, message="Task accepted")


@router.get("/", response_model=List[Task])
async def get_all_tasks():
    if _task_repo is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    return _task_repo.get_all_tasks()


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    if _task_repo is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    task = _task_repo.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return task


@router.delete("/{task_id}", response_model=TaskResponse)
async def cancel_task(task_id: str):
    if _task_repo is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    task = _task_repo.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
        raise HTTPException(status_code=400, detail=f"Task is already {task.status}")

    _task_repo.update_task_status(task_id, TaskStatus.CANCELLED)
    _nav_gateway.cancel_current_goal()

    return TaskResponse(id=task_id, status=TaskStatus.CANCELLED, message="Task cancel requested")
