---
name: wait
description: Make the robot wait in place for a specified duration
step_type: WAIT
params:
  durationSec: {type: float, description: "Duration to wait in seconds"}
---

# Wait Skill

Make the robot pause and wait at its current position for the specified duration.
Use this skill when the user asks the robot to wait, pause, stop for a while, or stay in place.
The duration is in seconds. If the user says "wait a minute", convert to 60 seconds.
