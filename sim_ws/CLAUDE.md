# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-robot AMR simulation platform using ROS 2 Jazzy and Gazebo Harmonic. The `sim_ws` workspace handles 3D simulation (Gazebo world, custom plugins, sensor bridging), while the sibling `robot_ws` workspace handles robot control (API, state, drivers). Both are orchestrated via Docker Compose with CycloneDDS.

## Build & Run Commands

```bash
# Build simulation workspace
cd /home/syncrobotic/Documents/SyncAI-Simulation/sim_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select syncai_demo_gz

# Source and launch
source install/setup.bash
ros2 launch syncai_demo_gz simulation.launch.py

# Build a single package (from sim_ws root)
colcon build --packages-select <package_name>
```

## Architecture

### Workspaces
- **sim_ws/** — Gazebo simulation (this workspace)
- **robot_ws/** — Robot control packages (syncai_common, syncai_robot_api, syncai_driver_manager, syncai_robot_state, syncai_bringup)
- **data/** — Per-robot configs (`system.ini`, `model.sdf`, `cyclonedds.xml`), read at launch time

### Simulation Package (`syncai_demo_gz`)
- **Custom Gazebo plugins** are built as shared libraries and installed to `lib/syncai_demo_gz/`. The launch file sets `GZ_SIM_SYSTEM_PLUGIN_PATH` automatically so Gazebo can find them.
- **DoorPlugin** (`src/DoorPlugin.cc`) — Sliding door system plugin controlling two prismatic joints via gz-transport service and topic. State published as `gz.msgs.StringMsg`. Bridged to ROS 2 via `ros_gz_bridge`.
- **Robot spawning** is dynamic: `simulation.launch.py` reads `~/data/*/system.ini` to discover robots, spawn their SDF models, and create per-robot bridge topics.
- **Topic bridging** (ROS 2 ↔ Gazebo) is consolidated into a single `parameter_bridge` node.

### Gazebo Libraries (Harmonic)
- gz-sim8, gz-plugin2, gz-transport13, gz-msgs10

### Docker
- `docker-compose.yml` at repo root orchestrates `sim` (GPU/X11) and `robot01` containers
- `sim` container volume-mounts `sim_ws/` and `data/`

## Coding Conventions

- **ROS 2 Jazzy**, C++20 or Python 3.10+
- **Build system**: `ament_cmake` (C++) or `ament_python` (Python), built with `colcon`
- **C++**: Inherit from `rclcpp::Node`, use `std::shared_ptr`, log via `RCLCPP_INFO/WARN/ERROR` macros, CamelCase classes, snake_case functions/variables
- **Python**: Type hints required, log via `node.get_logger()` not `print()`
- **Launch files**: Python-based, placed in `launch/` directory
- **Gazebo plugins**: Pure gz-sim system plugins (no ROS 2 dependency in plugin code). ROS 2 integration via `ros_gz_bridge` in launch files.
- **Topics/frame IDs**: Use parameters or constants, never hardcode
- **CMakeLists.txt**: `ament_package()` must be the last call
