import os
import structlog
from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, model_validator

from syncai_entity_manager.gateways.gazebo import GazeboGateway
from syncai_entity_manager.gateways.bridge import BridgeGateway
from syncai_entity_manager.repositories.entity import EntityRepo


class ModelType(str, Enum):
    BOX = 'box'
    VERTEX = 'vertex'


class Pose(BaseModel):
    x: float = Field(0.0, description='Position X (meters)')
    y: float = Field(0.0, description='Position Y (meters)')
    z: float = Field(0.0, description='Position Z (meters)')
    roll: float = Field(0.0, description='Rotation about X axis (radians)')
    pitch: float = Field(0.0, description='Rotation about Y axis (radians)')
    yaw: float = Field(0.0, description='Rotation about Z axis (radians)')


class BoxSize(BaseModel):
    sx: float = Field(..., description='Size X (meters)', gt=0, example=0.5)
    sy: float = Field(..., description='Size Y (meters)', gt=0, example=0.5)
    sz: float = Field(..., description='Size Z (meters)', gt=0, example=0.5)


class SpawnRequest(BaseModel):
    model_type: ModelType = Field(description='Type of model to spawn')
    entity_name: str = Field(description='Unique name in simulation, e.g. alarm_02')
    pose: Pose = Field(default_factory=Pose)
    size: Optional[BoxSize] = Field(None, description='Box dimensions, required when model_type is box')

    @model_validator(mode='after')
    def validate_size(self) -> 'SpawnRequest':
        if self.model_type == ModelType.BOX and self.size is None:
            raise ValueError('size is required when model_type is box')
        if self.model_type != ModelType.BOX and self.size is not None:
            raise ValueError('size should only be provided when model_type is box')
        return self


class EntityResponse(BaseModel):
    success: bool
    message: str


def init_entity_router(
    gazebo_gateway: GazeboGateway,
    bridge_gateway: BridgeGateway,
    entity_repo: EntityRepo,
) -> APIRouter:

    router = APIRouter(prefix="/api/v1/entities", tags=["entities"])

    @router.post("/", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
    async def spawn_entity(req: SpawnRequest):
        if entity_repo.exists(req.entity_name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f'Entity "{req.entity_name}" already exists'
            )

        # prepare sdf file
        if req.model_type == ModelType.BOX:
            sdf_string = GazeboGateway.generate_box_sdf(
                req.entity_name, req.size.sx, req.size.sy, req.size.sz
            )
        else:
            sdf_path = os.path.join(gazebo_gateway.models_dir, req.model_type.value, 'model.sdf')
            if not os.path.isfile(sdf_path):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Model type "{req.model_type.value}" not found')
            
            try:
                sdf_string = GazeboGateway.prepare_sdf(sdf_path, req.entity_name)
            except FileNotFoundError as err:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))

        # start spawn entity
        success, message = gazebo_gateway.spawn_entity(
            sdf_string=sdf_string,
            entity_name=req.entity_name,
            x=req.pose.x, y=req.pose.y, z=req.pose.z,
            roll=req.pose.roll, pitch=req.pose.pitch, yaw=req.pose.yaw,
        )

        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

        entity_repo.add(req.entity_name, req.model_type.value)
        bridge_gateway.add_bridge(req.entity_name, req.model_type.value)

        return EntityResponse(success=True, message=message)

    @router.delete("/{entity_name}", response_model=EntityResponse)
    async def delete_entity(entity_name: str):
        success, message = gazebo_gateway.delete_entity(entity_name)

        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

        bridge_gateway.remove_bridge(entity_name)
        entity_repo.remove(entity_name)

        return EntityResponse(success=True, message=message)

    return router
