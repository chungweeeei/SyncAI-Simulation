---
name: navigate_with_alert
description: Navigate to a position while activating visual/audio alerts
step_type: NAVIGATE_WITH_ALERT
params:
  x: {type: float, description: "X coordinate in meters"}
  y: {type: float, description: "Y coordinate in meters"}
  r: {type: float, description: "Rotation in degrees", default: 0.0}
---

# Navigate With Alert Skill

Navigate the robot to the specified position while activating alerts (LED strips, sounds).
Use this skill when the user asks the robot to move with caution, move with warning lights,
or navigate through areas that require alerting nearby people.
