import math


def navigate_to_pose(gateway, x: float, y: float, yaw: float) -> dict:
    yaw_rad = math.radians(yaw)
    success, message = gateway.navigate_to_pose(x, y, yaw_rad)
    return {"success": success, "message": message}


def navigate_with_alert(gateway, x: float, y: float, yaw: float) -> dict:
    yaw_rad = math.radians(yaw)
    success, message = gateway.navigate_with_alert(x, y, yaw_rad)
    return {"success": success, "message": message}
