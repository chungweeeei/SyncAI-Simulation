from typing import List

from pydantic import BaseModel, Field


class PlannedStep(BaseModel):
    skill: str = Field(..., description="Skill name from the available skills list")
    params: dict = Field(..., description="Parameters for the skill")


class TaskPlan(BaseModel):
    steps: List[PlannedStep] = Field(..., description="Ordered list of steps to execute")
