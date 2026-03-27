import os

TEMPORAL_SERVER_URL = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")


def get_task_queue(robot_id: str) -> str:
    return f"task-queue-{robot_id}"


def get_workflow_id(task_id: str) -> str:
    return f"task-{task_id}"
