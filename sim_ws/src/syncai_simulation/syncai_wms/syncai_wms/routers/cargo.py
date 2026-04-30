from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from syncai_wms.gateways.spawn import SpawnGateway
from syncai_wms.repositories.pending_cargo import PendingCargoRepo


class SpawnRequest(BaseModel):
    conveyor_id: str = Field(..., description="Conveyor device id", examples=["conveyor_01"])
    box_id: str = Field(..., description="Box id to spawn", examples=["box01"])


class SpawnResponse(BaseModel):
    success: bool
    message: str


class PendingCargoResponse(BaseModel):
    items: List[Dict[str, Any]]
    stamp_sec: Optional[float] = None


def init_cargo_router(
    spawn_gateway: SpawnGateway, pending_repo: PendingCargoRepo
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/wms/cargo", tags=["cargo"])

    @router.post("/spawn", response_model=SpawnResponse)
    def spawn_cargo(req: SpawnRequest) -> SpawnResponse:
        try:
            success, message = spawn_gateway.spawn(req.conveyor_id, req.box_id)
            return SpawnResponse(success=success, message=message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/pending", response_model=PendingCargoResponse)
    def get_pending() -> PendingCargoResponse:
        items, stamp_sec = pending_repo.snapshot()
        return PendingCargoResponse(items=items, stamp_sec=stamp_sec)

    return router
