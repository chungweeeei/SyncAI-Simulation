# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

```bash
source /opt/ros/jazzy/setup.bash
colcon build                                          # full workspace
colcon build --packages-select <pkg>                  # single package
colcon build --packages-select syncai_common syncai_robot_state syncai_robot_api  # after msg changes
source install/setup.bash                             # must re-source after build
```

When modifying `syncai_common/msg/RobotState.msg`, rebuild all downstream packages: `syncai_common` → `syncai_robot_state` → `syncai_robot_api`.

## Architecture

**ROS 2 Jazzy** workspace with hybrid C++/Python packages for an AMR (Autonomous Mobile Robot). Integrates with a sibling `sim_ws` (Gazebo Harmonic simulation) via DDS topics.

### Package Overview

| Package | Type | Purpose |
|---|---|---|
| `syncai_common` | ament_cmake | Custom ROS messages (`RobotState.msg`) |
| `syncai_robot_state` | ament_cmake (C++) | Aggregates odom/battery topics → publishes unified `robot_state` |
| `syncai_robot_api` | ament_python | FastAPI server + ROS node: REST API, task execution, Kafka state reporting |
| `syncai_bringup` | ament_cmake | Modular Nav2 launch files + config YAMLs |
| `syncai_driver_manager` | ament_cmake (C++) | Hardware driver abstraction, battery simulation |
| `third_party/robot_localization` | ament_cmake | EKF sensor fusion (odom encoder + IMU) |

### syncai_robot_api Layered Architecture

```
main.py (ROS Node + wiring)
├── repositories/     — Thread-safe in-memory stores (RobotRepo, TaskRepo)
├── subscribers/      — ROS topic → repository updates
├── gateways/         — External integrations (Nav2 action client, Kafka producer)
├── routers/          — FastAPI endpoints (tasks CRUD, robot state GET)
└── jobs/             — Daemon threads (periodic state sender, task executor)
```

FastAPI runs in a daemon thread alongside `rclpy.spin()` on the main thread. All shared state accessed via repos with `threading.Lock`.

### Key Patterns

- **Launch files** read `~/data/system.ini` at launch time for `robot_id`, used as namespace via `PushROSNamespace`
- **Nav2 config namespacing**: Use `<robot_namespace>` placeholder in YAML + `ReplaceString` substitution in launch files (see `ekf_launch.py`, `planner_launch.py`)
- **Nav2 lifecycle nodes**: Each Nav2 server launched individually with `lifecycle_nodes` parameter
- **Navigation futures**: Use `threading.Event` + `future.add_done_callback()` instead of polling loops (see `navigation.py`)
- **ROS Node attribute conflict**: Use `self._log` (not `self._logger`) for structlog in classes inheriting `rclpy.Node` — `_logger` is reserved by ROS

### Data Flow

```
Gazebo (sim_ws) → /scan, /odom, /imu, /battery_state
                      ↓
robot_localization (EKF) → /ekf_odom + odom→base_link TF
AMCL → /amcl_pose + map→odom TF
syncai_robot_state (C++) → /robot_state
                      ↓
syncai_robot_api (Python)
  ├→ Kafka topic "robot-state" (VDA5050 JSON via agent_schema.py)
  └→ HTTP API :3000 (/api/v1/tasks, /api/v1/robot/state)
```

### API Endpoints

- `POST /api/v1/tasks/` — Create task with MOVE/WAIT steps
- `GET /api/v1/tasks/` — List all tasks
- `GET /api/v1/tasks/{task_id}` — Get task by ID
- `DELETE /api/v1/tasks/{task_id}` — Cancel task
- `GET /api/v1/robot/state` — VDA5050-formatted robot state

### Per-Robot Configuration

`~/data/<robot_id>/system.ini`:
```ini
[identity]
robot_id=robot01
robot_name=SyncBot-01
model=AMR-X200

[spawn]
initial_pose_x=0.0
initial_pose_y=0.0
initial_pose_theta=0.0
```

## Environment Variables

| Variable | Default | Used by |
|---|---|---|
| `SYNCAI_SERVER_IP` | `10.8.101.86` | agent.py (Kafka :9092 + HTTP :8000) |
| `SYNCAI_API_PORT` | `3000` | server.py |
| `SYNCAI_DATA_DIR` | `~/data` | Dockerfile |
| `RMW_IMPLEMENTATION` | `rmw_cyclonedds_cpp` | docker-compose |

## Running

```bash
bash byobu_session.sh    # launches all Nav2 + API processes in byobu splits
```

Individual launches:
```bash
ros2 launch syncai_bringup amcl_launch.py
ros2 launch syncai_robot_api syncai_robot_api.launch.py
```

## Docker

```bash
docker-compose build robot01
docker-compose run -it robot01 bash
```

The robot container uses `network_mode: host` for DDS communication with the simulation container.

## Nav2 Plugin Names

ROS 2 Jazzy uses C++ namespace format (`::`) not the old `/` format:
```yaml
plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"  # correct
plugin: "nav2_regulated_pure_pursuit_controller/RegulatedPurePursuitController"   # wrong
```
