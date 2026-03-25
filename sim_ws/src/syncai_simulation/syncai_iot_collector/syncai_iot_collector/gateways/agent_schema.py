import time
from enum import Enum

from pydantic import BaseModel, Field

class IOTDeviceType(Enum):
    ALARM = "alarm"
    DOOR = "door"

class EventSeverity(Enum):
    LOW = "low"
    NORMAL = "normal"
    CRITICAL = "critical"

class EventDetail(BaseModel):
    device_type: IOTDeviceType = Field(..., description="The type of the device that triggered the event", example="alarm")
    device_id: str = Field(..., description="The ID of the device that triggered the event", example="alarm-01")

class EventData(BaseModel):
    location: str = Field(..., description="The location of the event", example="lobby")
    severity: EventSeverity = Field(..., description="The severity of the event", example="normal")
    detail: EventDetail = Field(..., description="The details of the event")

class EventMetaData(BaseModel):
    timestamp: int = Field(..., description="The timestamp of the event in milliseconds since epoch", example=1774403591)

class BuildingEvent(BaseModel):
    schema_version: str = Field(..., description="The version of the schema", alias="schemaVersion")
    event_type: str = Field(..., description="The type of the event", alias="eventType")
    data: EventData = Field(..., description="The data of the event")
    meta: EventMetaData = Field(..., description="The metadata of the event")


def build_building_event(severity: EventSeverity, detail: EventDetail, location: str = "lobby") -> BuildingEvent:

    event = BuildingEvent(
        schemaVersion="1.0",
        eventType="building-event-detected",
        data=EventData(
            location=location,
            severity=severity,
            detail=detail
            ),
        meta=EventMetaData(
            timestamp=int(time.time())
        )
    )

    return event