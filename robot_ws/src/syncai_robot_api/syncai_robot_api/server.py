import os
import threading
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from temporalio.client import Client

from syncai_robot_api.routers.task import init_task_router
from syncai_robot_api.routers.robot_state import init_robot_state_router
from syncai_robot_api.routers.map import init_map_router
from syncai_robot_api.repositories.robot.robot import RobotRepo
from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.gateways.robot import RobotGateway
from syncai_robot_api.temporal.shared import TEMPORAL_SERVER_URL


def create_app(
    robot_repo: RobotRepo,
    task_repo: TaskRepo,
    robot_gateway: RobotGateway,
    robot_id: str,
    map_name: str,
) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.temporal_client = await Client.connect(TEMPORAL_SERVER_URL)
        yield

    app = FastAPI(title="SyncAI Robot API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Content-Length", "Authorization"],
    )

    app.include_router(init_task_router(task_repo=task_repo, robot_gateway=robot_gateway, robot_id=robot_id))
    app.include_router(init_robot_state_router(robot_repo=robot_repo, task_repo=task_repo))
    app.include_router(init_map_router(map_name=map_name))
    return app


def start_api_server(
    logger: structlog.stdlib.BoundLogger,
    robot_repo: RobotRepo,
    task_repo: TaskRepo,
    robot_gateway: RobotGateway,
    robot_id: str,
    map_name: str,
):
    host = os.getenv("SYNCAI_API_HOST", "0.0.0.0")
    port = int(os.getenv("SYNCAI_API_PORT", "3000"))

    app = create_app(robot_repo=robot_repo, task_repo=task_repo, robot_gateway=robot_gateway, robot_id=robot_id, map_name=map_name)

    def _run():
        logger.info("[APIServer] Starting", host=host, port=port)
        uvicorn.run(app, host=host, port=port)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
