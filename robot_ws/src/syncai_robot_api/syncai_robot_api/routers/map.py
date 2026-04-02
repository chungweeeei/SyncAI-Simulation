import json
import os
import threading

import yaml
from fastapi import APIRouter, HTTPException, status
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field

from syncai_robot_api.helpers.map_helper import read_pgm_size
from syncai_robot_api.gateways.entity import EntityGateway


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

class Pose(BaseSchema):
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


class MapMetadata(BaseSchema):
    map_id: str = Field(..., description="Unique identifier for the map", alias="mapId")
    origin: Pose = Field(default_factory=Pose, description="Origin of the map")
    resolution: float = Field(..., description="Resolution of the map", examples=[0.05])
    width: int = Field(..., description="Width of the map", examples=[100])
    height: int = Field(..., description="Height of the map", examples=[100])


class Vertex(BaseSchema):
    name: str = Field("", description="Name of the vertex")
    pose: Pose = Field(default_factory=Pose, description="Pose of the vertex")


class CreateVertexRequest(BaseSchema):
    name: str = Field(..., description="Unique name of the vertex")
    pose: Pose = Field(default_factory=Pose, description="Pose of the vertex")


class VertexResponse(BaseSchema):
    success: bool
    message: str


class MapPayload(BaseSchema):
    map_metadata: MapMetadata = Field(..., alias="mapMetadata")
    vertexes: list[Vertex] = Field(default_factory=list)


def init_map_router(map_name: str, entity_gateway: EntityGateway) -> APIRouter:

    router = APIRouter(prefix="/api/v1/map", tags=["map"])
    _lock = threading.Lock()

    def _vertexes_path() -> Path:
        map_id = Path(os.path.expanduser(f"~/map/{map_name}.yaml")).stem
        return Path(os.path.expanduser(f"~/map/{map_id}_vertexes.json"))

    def _read_vertexes() -> list[dict]:
        path = _vertexes_path()
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return []

    def _write_vertexes(vertexes: list[dict]):
        with open(_vertexes_path(), "w") as f:
            json.dump(vertexes, f, indent=2)

    @router.get("/", response_model=MapPayload)
    async def get_map():
        map_yaml = os.path.expanduser(f"~/map/{map_name}.yaml")
        if not os.path.exists(map_yaml):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Map '{map_name}' not found",
            )

        try:
            with open(map_yaml) as f:
                map_config = yaml.load(f, Loader=yaml.CLoader)

            pgm_path = Path(map_yaml).parent / map_config["image"]
            width, height = read_pgm_size(pgm_path)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read map '{map_name}'",
            )

        origin = map_config.get("origin", [0.0, 0.0, 0.0])
        map_id = Path(map_yaml).stem

        with _lock:
            vertexes = _read_vertexes()

        return MapPayload(
            map_metadata=MapMetadata(
                map_id=map_id,
                origin=Pose(x=origin[0], y=origin[1], theta=origin[2]),
                resolution=map_config.get("resolution", 0.05),
                width=width,
                height=height,
            ),
            vertexes=[Vertex(name=v["name"], pose=Pose(**v["pose"])) for v in vertexes],
        )

    @router.post("/vertexes", response_model=VertexResponse, status_code=status.HTTP_201_CREATED)
    async def create_vertex(req: CreateVertexRequest):
        with _lock:
            vertexes = _read_vertexes()

        if any(v["name"] == req.name for v in vertexes):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Vertex '{req.name}' already exists",
            )

        success, message = entity_gateway.spawn_vertex(
            name=req.name, x=req.pose.x, y=req.pose.y, yaw=req.pose.theta,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=message,
            )

        with _lock:
            vertexes = _read_vertexes()
            vertexes.append({"name": req.name, "pose": {"x": req.pose.x, "y": req.pose.y, "theta": req.pose.theta}})
            _write_vertexes(vertexes)

        return VertexResponse(success=True, message=message)

    @router.delete("/vertexes/{vertex_name}", response_model=VertexResponse)
    async def delete_vertex(vertex_name: str):
        with _lock:
            vertexes = _read_vertexes()

        if not any(v["name"] == vertex_name for v in vertexes):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vertex '{vertex_name}' not found",
            )

        success, message = entity_gateway.delete_vertex(name=vertex_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=message,
            )

        with _lock:
            vertexes = _read_vertexes()
            vertexes = [v for v in vertexes if v["name"] != vertex_name]
            _write_vertexes(vertexes)

        return VertexResponse(success=True, message=message)

    return router
