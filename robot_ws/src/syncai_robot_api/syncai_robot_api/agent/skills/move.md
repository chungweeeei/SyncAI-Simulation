---
name: move
description: Navigate the robot to a target position on the map
step_type: MOVE
params:
  x: {type: float, description: "X coordinate in meters"}
  y: {type: float, description: "Y coordinate in meters"}
  r: {type: float, description: "Rotation in degrees", default: 0.0}
---

# Move Skill

Navigate the robot to the specified (x, y) position with a given rotation.
Use this skill when the user asks the robot to go to, move to, or navigate to a location.
If the user mentions a named location (e.g., "go to the lobby"), resolve the coordinates from the map vertex list.
The rotation parameter is in degrees. If not specified by the user, default to 0.0.
