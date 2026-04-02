def control_door(gateway, cmd_topic: str, state_topic: str, open: bool = True, timeout_sec: float = 10.0) -> dict:
    success, message = gateway.control_door(
        cmd_topic=cmd_topic,
        state_topic=state_topic,
        open=open,
        timeout_sec=timeout_sec,
    )
    return {"success": success, "message": message}
