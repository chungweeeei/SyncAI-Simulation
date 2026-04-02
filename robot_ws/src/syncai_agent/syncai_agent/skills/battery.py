def set_battery_level(gateway, level: float) -> dict:
    success, message = gateway.set_battery_level(level)
    return {"success": success, "message": message}
