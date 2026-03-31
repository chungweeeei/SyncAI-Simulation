import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.exceptions import ApplicationError, ActivityError

with workflow.unsafe.imports_passed_through():
    from syncai_robot_api.temporal.activities import RobotActivities
    from syncai_robot_api.temporal.converters import TaskWorkflowInput, StepResult


@workflow.defn
class TaskWorkflow:

    @workflow.run
    async def run(self, input: TaskWorkflowInput) -> StepResult:

        activity_map = {
            "MOVE": RobotActivities.execute_move,
            "WAIT": RobotActivities.execute_wait,
            "DOOR": RobotActivities.execute_door,
            "CHARGE": RobotActivities.execute_charge,
            "NAVIGATE_WITH_ALERT": RobotActivities.execute_navigate_with_alert,
        }

        try:
            for i, step in enumerate(input.steps):
                activity_fn = activity_map.get(step.step_type)
                if activity_fn is None:
                    raise ApplicationError(
                        f"Unknown step type: {step.step_type}", non_retryable=True
                    )
                
                
                result: StepResult = await workflow.execute_activity(
                    activity_fn,
                    step,
                    start_to_close_timeout=timedelta(minutes=60),
                )

                if not result.success:
                    # Update the task and step status in the repository
                    for j in range(i + 1, len(input.steps)):
                        remaining = input.steps[j]
                        workflow.logger.info(f"Cancelling step {remaining.step_index} due to failure at step {i}")

                    raise ApplicationError(result.message, non_retryable=True)

            return StepResult(success=True, message="Task completed")

        except asyncio.CancelledError:
            workflow.logger.info(f"Workflow cancelled for task {input.task_id}")
            raise
