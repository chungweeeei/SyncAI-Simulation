import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import structlog
from temporalio.client import Client
from temporalio.worker import Worker

from syncai_robot_api.gateways.robot import RobotGateway
from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.temporal.shared import TEMPORAL_SERVER_URL, get_task_queue
from syncai_robot_api.temporal.activities import RobotActivities
from syncai_robot_api.temporal.workflows import TaskWorkflow


def start_temporal_worker(
    logger: structlog.stdlib.BoundLogger,
    robot_gateway: RobotGateway,
    task_repo: TaskRepo,
    robot_id: str,
):
    """Start Temporal Worker in a daemon thread."""

    task_queue = get_task_queue(robot_id)
    ready = threading.Event()

    async def _run():
        client = await Client.connect(TEMPORAL_SERVER_URL)

        activities = RobotActivities(
            robot_gateway=robot_gateway,
            task_repo=task_repo,
            logger=logger,
        )

        worker = Worker(
            client=client,
            task_queue=task_queue,
            workflows=[TaskWorkflow],
            activities=[
                activities.execute_move,
                activities.execute_wait,
                activities.execute_door,
                activities.execute_charge,
                activities.execute_navigate_with_alert,
            ],
            activity_executor=ThreadPoolExecutor(max_workers=1),
        )

        logger.info(
            "[TemporalWorker] Started",
            task_queue=task_queue,
            server=TEMPORAL_SERVER_URL,
        )
        ready.set()
        await worker.run()

    def _thread_target():
        asyncio.run(_run())

    thread = threading.Thread(target=_thread_target, daemon=True)
    thread.start()
    ready.wait(timeout=10.0)

    logger.info("[TemporalWorker] Ready")
