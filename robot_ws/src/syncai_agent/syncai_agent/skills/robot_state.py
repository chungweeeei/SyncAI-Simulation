import math


def get_robot_state(state_store) -> dict:
    state = state_store()
    if state is None:
        return {"success": False, "message": "No robot state available yet"}
    return {
        "success": True,
        "robot_id": state["robot_id"],
        "pose": {
            "x": round(state["pose"]["x"], 3),
            "y": round(state["pose"]["y"], 3),
            "yaw_degrees": round(math.degrees(state["pose"]["yaw"]), 1),
        },
        "velocity": {
            "vx": round(state["velocity"]["vx"], 3),
            "vy": round(state["velocity"]["vy"], 3),
            "omega": round(state["velocity"]["omega"], 3),
        },
        "battery": {
            "percentage": round(state["battery"]["percentage"], 1),
            "voltage": round(state["battery"]["voltage"], 2),
        },
    }
