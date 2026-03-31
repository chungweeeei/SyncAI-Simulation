import asyncio

from temporalio.client import Client, WorkflowFailureError

from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.repositories.task.schema import Task, TaskStatus, StepStatus
from syncai_robot_api.gateways.robot import RobotGateway
from syncai_robot_api.temporal.workflows import TaskWorkflow
from syncai_robot_api.temporal.converters import TaskWorkflowInput
from syncai_robot_api.temporal.shared import get_task_queue, get_workflow_id


async def submit_task(
    task: Task,
    task_repo: TaskRepo,
    temporal_client: Client,
    robot_gateway: RobotGateway,
    robot_id: str,
) -> str:
    """Submit a task to the repository and start a Temporal workflow.

    Returns the workflow ID. Raises HTTPException-compatible errors.
    """
    success = task_repo.add_task(task)
    if not success:
        raise ValueError(f"Task {task.id} already exists")

    workflow_id = get_workflow_id(task.id)
    handle = await temporal_client.start_workflow(
        TaskWorkflow.run,
        TaskWorkflowInput.from_task(task),
        id=workflow_id,
        task_queue=get_task_queue(robot_id),
    )

    task_repo.update_workflow_id(task.id, workflow_id)
    task_repo.update_task_status(task.id, TaskStatus.IN_PROGRESS)
    task_repo.set_active_task(task.id)

    async def _on_workflow_complete(wf_handle, tid: str):
        try:
            await wf_handle.result()
            task_repo.update_task_status(tid, TaskStatus.COMPLETED)
        except WorkflowFailureError as e:
            t = task_repo.get_task(tid)
            if t and t.status == TaskStatus.CANCELLED:
                return

            error_msg = e.cause.message if e.cause else str(e)
            task_repo.update_task_status(tid, TaskStatus.FAILED, error_msg=error_msg)
            t = task_repo.get_task(tid)
            if t:
                for i, step in enumerate(t.payload.steps):
                    if step.status == StepStatus.PENDING:
                        task_repo.update_step_status(tid, i, StepStatus.CANCELLED)
        except Exception as e:
            task_repo.update_task_status(tid, TaskStatus.FAILED, error_msg=str(e))
        finally:
            task_repo.set_completed_at(tid)
            task_repo.clear_active_task()

    asyncio.create_task(_on_workflow_complete(handle, task.id))

    return workflow_id
