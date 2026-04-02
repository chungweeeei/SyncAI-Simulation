from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from syncai_entity_manager.gateways.gazebo import GazeboGateway
from syncai_entity_manager.gateways.bridge import BridgeGateway
from syncai_entity_manager.repositories.entity import EntityRepo
from syncai_entity_manager.routers.entity import init_entity_router


def create_app(
    gazebo_gateway: GazeboGateway,
    bridge_gateway: BridgeGateway,
    entity_repo: EntityRepo,
) -> FastAPI:

    app = FastAPI(title="SyncAI Entity Manager", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Content-Length", "Authorization"],
    )

    app.include_router(init_entity_router(
        gazebo_gateway=gazebo_gateway,
        bridge_gateway=bridge_gateway,
        entity_repo=entity_repo,
    ))

    return app
