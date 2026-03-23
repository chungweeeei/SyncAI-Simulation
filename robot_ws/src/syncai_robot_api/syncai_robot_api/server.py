import os
import threading

import structlog
import uvicorn
from fastapi import FastAPI

from syncai_robot_api.routers.task_router import router as task_router
from syncai_robot_api.routers.task_router import configure as configure_task_router
from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.gateways.navigation import NavigationGateway


def create_app(task_repo: TaskRepo, nav_gateway: NavigationGateway) -> FastAPI:
    app = FastAPI(title="SyncAI Robot API", version="0.1.0")

    configure_task_router(task_repo=task_repo, nav_gateway=nav_gateway)
    app.include_router(task_router)

    return app


def start_api_server(
    logger: structlog.stdlib.BoundLogger,
    task_repo: TaskRepo,
    nav_gateway: NavigationGateway,
):
    host = os.getenv("SYNCAI_API_HOST", "0.0.0.0")
    port = int(os.getenv("SYNCAI_API_PORT", "3000"))

    app = create_app(task_repo=task_repo, nav_gateway=nav_gateway)

    def _run():
        logger.info("[APIServer] Starting", host=host, port=port)
        uvicorn.run(app, host=host, port=port, log_level="warning")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
