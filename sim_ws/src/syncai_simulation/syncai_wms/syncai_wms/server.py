import os
import threading
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from syncai_wms.db.bootstrap import bootstrap, ensure_database_exists
from syncai_wms.db.session import create_engine_and_factory, get_db_url
from syncai_wms.gateways.spawn import SpawnGateway
from syncai_wms.repositories.cell.cell import CellRepo
from syncai_wms.repositories.pending_cargo import PendingCargoRepo
from syncai_wms.routers.cargo import init_cargo_router
from syncai_wms.routers.cell import init_cell_router


def create_app(
    logger: structlog.stdlib.BoundLogger,
    spawn_gateway: SpawnGateway,
    pending_repo: PendingCargoRepo,
    cell_repo: CellRepo,
) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await ensure_database_exists(logger)
        engine, session_factory = create_engine_and_factory(get_db_url())
        await bootstrap(logger=logger, engine=engine)
        cell_repo.bind_session_factory(session_factory)
        app.state.engine = engine
        app.state.session_factory = session_factory
        try:
            yield
        finally:
            await engine.dispose()

    app = FastAPI(title="SyncAI WMS API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Content-Length", "Authorization"],
    )
    app.include_router(
        init_cargo_router(spawn_gateway=spawn_gateway, pending_repo=pending_repo)
    )
    app.include_router(init_cell_router(cell_repo=cell_repo))
    return app


def start_api_server(
    logger: structlog.stdlib.BoundLogger,
    spawn_gateway: SpawnGateway,
    pending_repo: PendingCargoRepo,
    cell_repo: CellRepo,
) -> None:
    host = os.getenv("SYNCAI_WMS_HOST", "0.0.0.0")
    port = int(os.getenv("SYNCAI_WMS_PORT", "8100"))

    app = create_app(
        logger=logger,
        spawn_gateway=spawn_gateway,
        pending_repo=pending_repo,
        cell_repo=cell_repo,
    )

    def _run() -> None:
        logger.info("[WMSServer] starting", host=host, port=port)
        uvicorn.run(app, host=host, port=port)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
