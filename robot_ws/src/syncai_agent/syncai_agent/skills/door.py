def control_door(modbus_gateway, cmd_topic: str, open: bool = True, timeout_sec: float = 10.0) -> dict:
    success, message = modbus_gateway.control_door(
        cmd_topic=cmd_topic,
        open=open,
        timeout_sec=timeout_sec,
    )
    return {"success": success, "message": message}
