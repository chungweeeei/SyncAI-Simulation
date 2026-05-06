from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FunctionTypeCategory(str, Enum):
    # Conceptually aligned with backend StepType (CHARGE/WAIT/PICKUP/DROPOFF)
    # in backend/src/modules/task/enums/task.enum.ts
    CHARGER = "CHARGER"
    WAITING = "WAITING"
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"
    GENERAL = "GENERAL"


class CellCreate(BaseModel):
    map_id: str = Field(
        ..., description="Map id this cell belongs to", examples=["testmap"]
    )
    area_id: str = Field(..., description="Area grouping label", examples=["default"])
    cell_position_x: float = Field(..., description="World X (m)", examples=[1.5])
    cell_position_y: float = Field(..., description="World Y (m)", examples=[2.0])
    cell_orientation_r: float = Field(
        default=0.0,
        description="Approach orientation in degrees (yaw); 0 = +X axis",
        examples=[0.0],
    )
    display_name: str = Field(
        ...,
        description="Human-readable cell name (unique within a map)",
        examples=["dropoff_a"],
    )
    function_type_category: FunctionTypeCategory = Field(
        ..., description="High-level cell function", examples=["DROPOFF"]
    )
    function_type_name: str = Field(
        ..., description="Sub-type label", examples=["AMR_DROPOFF"]
    )
    occupied_by: Optional[str] = Field(
        default=None, description="Robot id occupying this cell, if any"
    )


class CellUpdate(BaseModel):
    # map_id is intentionally excluded — a cell does not move between maps.
    model_config = ConfigDict(extra="forbid")

    area_id: Optional[str] = None
    cell_position_x: Optional[float] = None
    cell_position_y: Optional[float] = None
    cell_orientation_r: Optional[float] = None
    display_name: Optional[str] = None
    function_type_category: Optional[FunctionTypeCategory] = None
    function_type_name: Optional[str] = None
    occupied_by: Optional[str] = None


_CELL_RESPONSE_EXAMPLE = {
    "uuid": "4386af1d-ffb9-42bc-89f5-9ccd41f887ed",
    "map_id": "testmap",
    "area_id": "default",
    "cell_position_x": 4.45,
    "cell_position_y": -1.4,
    "cell_orientation_r": 90.0,
    "display_name": "dropoff_a",
    "function_type_category": "DROPOFF",
    "function_type_name": "AMR_DROPOFF",
    "occupied_by": "robot01",
}


class CellResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": _CELL_RESPONSE_EXAMPLE},
    )

    uuid: UUID = Field(..., examples=[_CELL_RESPONSE_EXAMPLE["uuid"]])
    map_id: str = Field(..., examples=["testmap"])
    area_id: str = Field(..., examples=["default"])
    cell_position_x: float = Field(..., examples=[4.45])
    cell_position_y: float = Field(..., examples=[-1.4])
    cell_orientation_r: float = Field(..., examples=[90.0])
    display_name: str = Field(..., examples=["dropoff_a"])
    function_type_category: FunctionTypeCategory = Field(..., examples=["DROPOFF"])
    function_type_name: str = Field(..., examples=["AMR_DROPOFF"])
    occupied_by: Optional[str] = Field(..., examples=["robot01"])


class CellListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"cells": [_CELL_RESPONSE_EXAMPLE]}}
    )

    cells: List[CellResponse]


class OccupyRequest(BaseModel):
    robot_id: str = Field(
        ...,
        description="Robot id to mark as the cell's occupier",
        examples=["robot01"],
    )


class ReleaseRequest(BaseModel):
    robot_id: str = Field(
        ...,
        description="Robot id whose occupancy on every cell should be cleared",
        examples=["robot01"],
    )


class ReleaseResponse(BaseModel):
    robot_id: str = Field(..., examples=["robot01"])
    cleared: int = Field(
        ...,
        description="Number of cells that were occupied by this robot and got cleared",
        examples=[1],
    )
