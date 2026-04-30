import os
import threading

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from syncai_wms.gateways.spawn import SpawnGateway
from syncai_wms.repositories.pending_cargo import PendingCargoRepo
from syncai_wms.routers.cargo import init_cargo_router


def create_app(spawn_gateway: SpawnGateway, pending_repo: PendingCargoRepo) -> FastAPI:
    app = FastAPI(title="SyncAI WMS API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Content-Length", "Authorization"],
    )
    app.include_router(
        init_cargo_router(spawn_gateway=spawn_gateway, pending_repo=pending_repo)
    )
    return app


def start_api_server(
    logger: structlog.stdlib.BoundLogger,
    spawn_gateway: SpawnGateway,
    pending_repo: PendingCargoRepo,
) -> None:
    host = os.getenv("SYNCAI_WMS_HOST", "0.0.0.0")
    port = int(os.getenv("SYNCAI_WMS_PORT", "8100"))

    app = create_app(spawn_gateway=spawn_gateway, pending_repo=pending_repo)

    def _run() -> None:
        logger.info("[WMSServer] starting", host=host, port=port)
        uvicorn.run(app, host=host, port=port)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
