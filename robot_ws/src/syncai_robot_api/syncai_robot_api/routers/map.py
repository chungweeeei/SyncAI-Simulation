import json
import os

import yaml
from fastapi import APIRouter, HTTPException, status
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field

from syncai_robot_api.helpers.map_helper import read_pgm_size

class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

class Pose(BaseSchema):
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


class MapMetadata(BaseSchema):
    map_id: str = Field(..., description="Unique identifier for the map", alias="mapId")
    origin: Pose = Field(..., description="Origin of the map", default_factory=Pose)
    resolution: float = Field(..., description="Resolution of the map", example=0.05)
    width: int = Field(..., description="Width of the map", example=100)
    height: int = Field(..., description="Height of the map", example=100)


class Vertex(BaseSchema):
    name: str = Field("", description="Name of the vertex")
    pose: Pose = Field(default_factory=Pose, description="Pose of the vertex")


class MapPayload(BaseSchema):
    map_metadata: MapMetadata = Field(..., alias="mapMetadata")
    vertexes: list[Vertex] = Field(default_factory=list)


def init_map_router(map_name: str) -> APIRouter:

    router = APIRouter(prefix="/api/v1/map", tags=["map"])

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

        # Load vertexes
        vertexes_path = Path(map_yaml).parent / f"{map_id}_vertexes.json"
        vertexes = []
        if vertexes_path.exists():
            with open(vertexes_path) as f:
                vertexes = json.load(f)

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

    return router
