---
name: charge
description: Navigate to a charging station and charge the robot battery
step_type: CHARGE
params:
  x: {type: float, description: "X coordinate near charging station"}
  y: {type: float, description: "Y coordinate near charging station"}
  r: {type: float, description: "Rotation in degrees", default: 0.0}
---

# Charge Skill

This is a single atomic operation that navigates to a charging station and initiates charging.
Do NOT use the move skill before or after this skill — charge already handles navigation internally.
Use this skill when the user asks to charge, recharge, go to charge, or go to a charging station.
If the user mentions a named location, resolve it from the map vertexes.
If no specific charging station is mentioned, look for a vertex with "charge" or "charging" in its name.
