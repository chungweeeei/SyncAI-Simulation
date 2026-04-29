# Integration tests

End-to-end scripts that exercise the cargo pipeline across the
`SyncAI-Omniverse` simulation and this `robot_ws` ROS 2 stack. They drive
`/robot01` via nav2 goals and operate the conveyor + cargo topics
published by Isaac Sim's ConveyorScript.

These are **not** colcon unit tests. They are runtime scripts that
require a live sim + a running nav2 stack; they intentionally live
outside `src/<pkg>/test/` so they don't get pulled into `colcon test`.

## Prerequisites

- `syncai-simulation` container running `scripts/run_sim.py` with the
  multi-box ConveyorScript loaded (look for `[conveyor]   spawn: topic=...`
  on startup).
- `syncai-robot01` (or any ROS 2 jazzy container with cyclonedds joined
  to the same domain) — that's where these scripts run.
- `robot01` nav2 stack alive (`/robot01/goal_pose`, `/robot01/odom`).
- The drop area authored by `SyncAI-Omniverse/config/sim_config.yaml`
  (default zone id `dropoff_a`).

## Map ↔ USD calibration baked in

```
USD world = map + (1.45, 2.71)
pickup    : map (-3.45,  4.34)  ↔ USD (-2.00, 7.05)
staging   : map ( 4.50, -1.35)  ↔ USD ( 5.95, 1.36)
drop_pose : USD (5.85, -0.29, 1.0)  -- handled inside sim
```

If you change `dropoff_a` or recalibrate the map, update the constants
at the top of each script.

## Tests

### `test_multibox.py`

Three cycles + a deliberate box-mismatch reject:

1. Pickup `box01` → drop at `dropoff_a` (`dropped:box01@dropoff_a`)
2. `spawn_cmd` → `box02` → pickup → drop
3. `spawn_cmd` → `box03` → pickup → drop, with a `box01:dropoff_a`
   payload while carrying `box03` to verify `drop_rejected:box_mismatch`.

```bash
docker exec syncai-robot01 bash -lc \
  '. /opt/ros/jazzy/setup.bash && python3 -u integration_tests/test_multibox.py'
```

(Or copy into `/tmp` inside the container if `/integration_tests` isn't
mounted; the workspace is normally mounted at `/home/ubuntu/robot_ws`.)

### `test_one_cycle.py`

Spawn the next box (auto-incremented `boxNN`) then run a single
pickup→drop cycle. Useful for adding more boxes to an already-running
sim without restarting.

```bash
docker exec syncai-robot01 bash -lc \
  '. /opt/ros/jazzy/setup.bash && python3 -u integration_tests/test_one_cycle.py'
```

## Notes

- Both scripts use `_reset_N` sentinels between dedupe-gated commands
  (drop_cmd / spawn_cmd) — required by ConveyorScript's text-based
  dedupe (see memory `feedback_drop_cmd_dedupe.md`).
- Status format expected: `carried:<box_id>@<robot_name>`,
  `dropped:<box_id>@<zone_id>`, `drop_rejected:box_mismatch`.
- These scripts assume `robot01` only. Multi-robot would need adapting
  the topic prefixes.
