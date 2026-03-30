import math
import asyncio
from dataclasses import dataclass

import structlog
from temporalio import activity
from temporalio.exceptions import ApplicationError

from syncai_robot_api.gateways.robot import RobotGateway
from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.repositories.task.schema import StepStatus
from syncai_robot_api.temporal.converters import StepInput, StepResult


@dataclass
class RobotActivities:
    robot_gateway: RobotGateway
    task_repo: TaskRepo
    logger: structlog.stdlib.BoundLogger

    @activity.defn
    def execute_move(self, input: StepInput) -> StepResult:
        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.IN_PROGRESS)
        self.task_repo.update_current_step_index(input.task_id, input.step_index)

        success, msg = self.robot_gateway.navigate_to_pose(
            x=input.params["x"], y=input.params["y"], yaw=input.params["r"]
        )

        status = StepStatus.COMPLETED if success else StepStatus.FAILED
        self.task_repo.update_step_status(
            input.task_id, input.step_index, status,
            error_msg=msg if not success else None
        )

        return StepResult(success=success, message=msg)

    @activity.defn
    async def execute_wait(self, input: StepInput) -> StepResult:
        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.IN_PROGRESS)
        self.task_repo.update_current_step_index(input.task_id, input.step_index)

        await asyncio.sleep(input.params["durationSec"])

        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.COMPLETED)
        return StepResult(success=True, message="Wait completed")

    @activity.defn
    def execute_charge(self, input: StepInput) -> StepResult:
        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.IN_PROGRESS)
        self.task_repo.update_current_step_index(input.task_id, input.step_index)

        yaw_rad = math.radians(input.params.get("r", 0.0))

        success, msg = self.robot_gateway.charge(
            x=input.params["x"],
            y=input.params["y"],
            yaw=yaw_rad,
            dock_id="charging_station",
            dock_type="simple_charging_dock",
        )

        status = StepStatus.COMPLETED if success else StepStatus.FAILED
        self.task_repo.update_step_status(
            input.task_id, input.step_index, status,
            error_msg=msg if not success else None
        )
            
        return StepResult(success=success, message=msg)

    @activity.defn
    def execute_door(self, input: StepInput) -> StepResult:
        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.IN_PROGRESS)
        self.task_repo.update_current_step_index(input.task_id, input.step_index)

        success, msg = self.robot_gateway.control_door(
            cmd_topic=input.params.get("cmd_topic", "/door/door_01/cmd_topic"),
            state_topic=input.params.get("state_topic", "/door/door_01/state"),
            open=input.params["open"],
            timeout_sec=input.params.get("timeout_sec", 10.0),
        )

        status = StepStatus.COMPLETED if success else StepStatus.FAILED
        self.task_repo.update_step_status(
            input.task_id, input.step_index, status,
            error_msg=msg if not success else None
        )

        return StepResult(success=success, message=msg)
