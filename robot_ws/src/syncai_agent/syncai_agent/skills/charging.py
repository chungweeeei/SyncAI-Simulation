import math


def charge(gateway, x: float, y: float, yaw: float) -> dict:
    yaw_rad = math.radians(yaw)
    success, message = gateway.charge(x, y, yaw_rad)
    return {"success": success, "message": message}
