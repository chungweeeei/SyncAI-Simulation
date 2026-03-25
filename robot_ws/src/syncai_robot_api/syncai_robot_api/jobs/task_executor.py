import time
import structlog
import threading

from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.repositories.task.schema import TaskStatus, StepStatus, StepType
from syncai_robot_api.gateways.robot import RobotGateway


class TaskExecutorJob:

    def __init__(self,
        logger: structlog.stdlib.BoundLogger,
        task_repo: TaskRepo,
        robot_gateway: RobotGateway
    ):
        self._logger = logger
        self._task_repo = task_repo
        self._robot_gateway = robot_gateway

    def register(self, start_delay: float, interval: float):
        self._logger.info(
            "[TaskExecutorJob][register] Registering task executor job"
        )
        self._start_delay = start_delay
        self._interval = interval

        job = threading.Thread(target=self.run, daemon=True)
        job.start()

    def run(self):
        time.sleep(self._start_delay)

        while True:
            task = self._task_repo.get_next_pending_task()
            if task is None:
                time.sleep(self._interval)
                continue
            
            # blocking call to execute the task
            self._execute_task(task.id)
            time.sleep(self._interval)

    def _execute_task(self, task_id: str):
        task = self._task_repo.get_task(task_id)
        if task is None:
            return

        self._logger.info("[TaskExecutorJob] Starting task", task_id=task_id)

        self._task_repo.set_active_task(task_id)
        self._task_repo.update_task_status(task_id, TaskStatus.IN_PROGRESS)

        steps = task.payload.steps
        for i, step in enumerate(steps):
            # Check if task was cancelled before executing each step
            current = self._task_repo.get_task(task_id)
            if current and current.status == TaskStatus.CANCELLED:
                for j in range(i, len(steps)):
                    self._task_repo.update_step_status(task_id, j, StepStatus.CANCELLED)
                break

            self._task_repo.update_current_step_index(task_id, i)
            self._task_repo.update_step_status(task_id, i, StepStatus.IN_PROGRESS)

            self._logger.info(
                "[TaskExecutorJob] Executing step",
                task_id=task_id, step_id=step.id, step_type=step.type
            )
            
            # handle each step type
            if step.type == StepType.MOVE:
                success, msg = self._robot_gateway.navigate_to_pose(
                    x=step.params.x, y=step.params.y, yaw=step.params.r
                )
            elif step.type == StepType.DOOR:
                success, msg = self._robot_gateway.control_door(
                    cmd_topic="/door/door_01/cmd_topic",
                    state_topic="/door/door_01/state",
                    open=step.params.open,
                    timeout_sec=10.0
                )
            elif step.type == StepType.WAIT:
                time.sleep(step.params.durationSec)
                success, msg = True, "Wait completed"
            else:
                success, msg = False, f"Unknown step type: {step.type}"

            if success:
                self._task_repo.update_step_status(task_id, i, StepStatus.COMPLETED)
                self._logger.info(
                    "[TaskExecutorJob] Step completed",
                    task_id=task_id, step_id=step.id
                )
            else:
                self._task_repo.update_step_status(task_id, i, StepStatus.FAILED, error_msg=msg)

                current = self._task_repo.get_task(task_id)
                if not (current and current.status == TaskStatus.CANCELLED):
                    self._task_repo.update_task_status(task_id, TaskStatus.FAILED, error_msg=msg)

                for j in range(i + 1, len(steps)):
                    self._task_repo.update_step_status(task_id, j, StepStatus.CANCELLED)

                self._logger.info(
                    "[TaskExecutorJob] Step failed",
                    task_id=task_id, step_id=step.id, error=msg
                )
                break
        
        self._task_repo.update_task_status(task_id, TaskStatus.COMPLETED)
        self._logger.info("[TaskExecutorJob] Task completed", task_id=task_id)

        self._task_repo.clear_active_task()

def init_task_executor_job(
    logger: structlog.stdlib.BoundLogger,
    task_repo: TaskRepo,
    robot_gateway: RobotGateway
) -> None:
    job = TaskExecutorJob(logger=logger, task_repo=task_repo, robot_gateway=robot_gateway)
    job.register(start_delay=2.0, interval=1.0)
