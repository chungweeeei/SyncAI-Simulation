from fastapi import APIRouter, HTTPException, status

from syncai_robot_api.repositories.robot.robot import RobotRepo
from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.gateways.agent_schema import Vda5050State, build_external_robot_state


def init_robot_state_router(robot_repo: RobotRepo, task_repo: TaskRepo) -> APIRouter:

    router = APIRouter(prefix="/api/v1/robot", tags=["robot"])

    @router.get("/state", response_model=Vda5050State)
    async def get_robot_state():
        robot_state = robot_repo.get_robot_state()
        if robot_state is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Robot state not yet available"
            )

        active_task = task_repo.get_active_task()
        return build_external_robot_state(robot_state, active_task)

    return router
