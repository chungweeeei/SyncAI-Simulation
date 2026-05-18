import math
import asyncio
from dataclasses import dataclass

import structlog
from temporalio import activity

from syncai_robot_api.gateways.robot import RobotGateway
from syncai_robot_api.gateways.modbus import ModbusGateway
from syncai_robot_api.gateways.cargo import CargoGateway
from syncai_robot_api.gateways.wms import WmsGateway
from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.repositories.task.schema import StepStatus
from syncai_robot_api.temporal.converters import StepInput, StepResult


@dataclass
class RobotActivities:
    robot_gateway: RobotGateway
    modbus_gateway: ModbusGateway
    cargo_gateway: CargoGateway
    wms_gateway: WmsGateway
    task_repo: TaskRepo
    robot_id: str
    logger: structlog.stdlib.BoundLogger

    def _finalize_step_status(self, input: StepInput, success: bool, msg: str) -> StepResult:
        # If cancel was requested while this activity was running, the step is
        # CANCELLED regardless of the gateway outcome.
        if self.task_repo.is_cancel_requested():
            self.task_repo.update_step_status(
                input.task_id, input.step_index, StepStatus.CANCELLED,
                error_msg="Cancelled by user"
            )
            return StepResult(success=False, message="Cancelled by user")

        status = StepStatus.COMPLETED if success else StepStatus.FAILED
        self.task_repo.update_step_status(
            input.task_id, input.step_index, status,
            error_msg=msg if not success else None
        )
        return StepResult(success=success, message=msg)

    @activity.defn
    def execute_move(self, input: StepInput) -> StepResult:
        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.IN_PROGRESS)
        self.task_repo.update_current_step_index(input.task_id, input.step_index)

        yaw_rad = math.radians(input.params.get("r", 0.0))
        cell_id = input.params.get("cell_id")

        # Robot is about to leave its current cell — release it immediately so
        # the cell is free during transit, not only after arrival.
        self.wms_gateway.release_robot(robot_id=self.robot_id)

        success, msg = self.robot_gateway.navigate_to_pose(
            x=input.params["x"], y=input.params["y"], yaw=yaw_rad
        )

        if success and cell_id and not self.task_repo.is_cancel_requested():
            # Arrived at a known cell — claim it
            self.wms_gateway.occupy_cell(cell_id=cell_id, robot_id=self.robot_id)
        # On failure, cancel, or no destination cell, robot stays free (already released).

        return self._finalize_step_status(input, success, msg)

    @activity.defn
    async def execute_wait(self, input: StepInput) -> StepResult:
        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.IN_PROGRESS)
        self.task_repo.update_current_step_index(input.task_id, input.step_index)

        try:
            await asyncio.sleep(input.params["durationSec"])
        except asyncio.CancelledError:
            self.task_repo.update_step_status(
                input.task_id, input.step_index, StepStatus.CANCELLED,
                error_msg="Cancelled by user"
            )
            raise

        return self._finalize_step_status(input, True, "Wait completed")

    @activity.defn
    def execute_charge(self, input: StepInput) -> StepResult:
        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.IN_PROGRESS)
        self.task_repo.update_current_step_index(input.task_id, input.step_index)

        yaw_rad = math.radians(input.params.get("r", 0.0))

        success, msg = self.robot_gateway.charge(
            x=input.params["x"],
            y=input.params["y"],
            yaw=yaw_rad,
        )

        return self._finalize_step_status(input, success, msg)

    @activity.defn
    def execute_door(self, input: StepInput) -> StepResult:
        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.IN_PROGRESS)
        self.task_repo.update_current_step_index(input.task_id, input.step_index)

        success, msg = self.modbus_gateway.control_door(
            cmd_topic=input.params.get("cmd_topic", "/door/door_01/cmd_topic"),
            open=input.params["open"],
            timeout_sec=input.params.get("timeout_sec", 10.0),
            coil_address=input.params.get("coil_address"),
        )

        return self._finalize_step_status(input, success, msg)

    @activity.defn
    def execute_pickup(self, input: StepInput) -> StepResult:
        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.IN_PROGRESS)
        self.task_repo.update_current_step_index(input.task_id, input.step_index)

        conveyor_id = input.params["conveyor_id"]
        timeout = input.params.get("verify_timeout_sec", 10.0)

        success, msg, box_id = self.modbus_gateway.read_conveyor_box_id(conveyor_id)
        if success:
            success, msg = self.cargo_gateway.pickup(
                conveyor_id=conveyor_id, box_id=box_id
            )
        if success:
            success, msg = self.modbus_gateway.verify_pickup(
                conveyor_id=conveyor_id, timeout_sec=timeout
            )
            if success and not self.task_repo.is_cancel_requested():
                self.cargo_gateway.mark_carried(box_id, conveyor_id)

        return self._finalize_step_status(input, success, msg)

    @activity.defn
    def execute_dropoff(self, input: StepInput) -> StepResult:
        self.task_repo.update_step_status(input.task_id, input.step_index, StepStatus.IN_PROGRESS)
        self.task_repo.update_current_step_index(input.task_id, input.step_index)

        zone_id = input.params["zone_id"]
        timeout = input.params.get("verify_timeout_sec", 10.0)

        success, msg, conveyor_id = self.cargo_gateway.dropoff(zone_id=zone_id)
        if success:
            success, msg = self.modbus_gateway.verify_dropoff(
                conveyor_id=conveyor_id, timeout_sec=timeout
            )
            if success and not self.task_repo.is_cancel_requested():
                self.cargo_gateway.clear_carried()

        return self._finalize_step_status(input, success, msg)
