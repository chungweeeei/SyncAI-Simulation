from pydantic import BaseModel, Field

class RobotPose(BaseModel):
    x: float = Field(..., description="The x-coordinate of the robot's position.")
    y: float = Field(..., description="The y-coordinate of the robot's position.")
    yaw: float = Field(..., description="The yaw (orientation) of the robot in radians.")

class RobotBattery(BaseModel):
    percentage: float = Field(..., description="The battery percentage of the robot.")
    voltage: float = Field(..., description="The voltage of the robot's battery in volts.")

class RobotState(BaseModel):
    timestamp: float = Field(..., description="The timestamp of the robot state in seconds since the epoch.")
    robot_id: str = Field(..., description="The unique identifier of the robot.")
    robot_name: str = Field(..., description="The name of the robot.")
    model: str = Field(..., description="The model of the robot.")
    map: str = Field(..., description="The map on which the robot is operating.")
    pose: RobotPose = Field(..., description="The current pose of the robot.")
    battery: RobotBattery = Field(..., description="The current battery status of the robot.")