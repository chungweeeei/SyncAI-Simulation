import time
import uuid
from typing import List

from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, Request, status

from syncai_robot_api.agent.nlp.task_planner import TaskPlannerService
from syncai_robot_api.agent.llm.schemas import PlannedStep
from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.repositories.task.schema import (
    Task,
    TaskActionType,
    TaskPayload,
    TaskStatus,
)
from syncai_robot_api.gateways.robot import RobotGateway
from syncai_robot_api.helpers.task_helper import submit_task


class CommandRequest(BaseModel):
    command: str = Field(..., description="Natural language command", example="Go to the charging station and charge")


class CommandResponse(BaseModel):
    task_id: str
    status: TaskStatus
    plan: List[PlannedStep]
    message: str


def init_agent_router(
    task_planner: TaskPlannerService,
    task_repo: TaskRepo,
    robot_gateway: RobotGateway,
    robot_id: str,
) -> APIRouter:

    router = APIRouter(prefix="/api/v1/agent", tags=["agent"])

    @router.post("/command", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
    async def submit_command(req: CommandRequest, request: Request):
        # Step 1: Use LLM to plan the task
        try:
            plan = await task_planner.plan_task(req.command)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to plan task: {str(e)}",
            )

        if not plan.steps:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="LLM produced an empty plan",
            )

        # Step 2: Convert plan to Task steps
        try:
            steps = task_planner.convert_to_steps(plan)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid plan parameters: {str(e)}",
            )

        # Step 3: Build Task and submit to pipeline
        task = Task(
            action=TaskActionType.TASK,
            id=str(uuid.uuid4())[:8],
            timestamp=time.time(),
            payload=TaskPayload(steps=steps),
        )

        temporal_client = request.app.state.temporal_client
        try:
            await submit_task(
                task=task,
                task_repo=task_repo,
                temporal_client=temporal_client,
                robot_gateway=robot_gateway,
                robot_id=robot_id,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start workflow: {str(e)}",
            )

        return CommandResponse(
            task_id=task.id,
            status=TaskStatus.IN_PROGRESS,
            plan=plan.steps,
            message="Task created from command",
        )

    return router
