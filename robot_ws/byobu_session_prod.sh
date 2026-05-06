#!/bin/bash
# =============================================================================
# SyncAI Robot Byobu Session — PROD profile
#   Collapses Nav2 stack into a single window driven by nav2_bringup_launch.py
#   (one master lifecycle_manager). Use byobu_session.sh for the dev profile
#   where each Nav2 module has its own window + lifecycle_manager.
# Usage: bash byobu_session_prod.sh
# =============================================================================

SESSION_NAME="syncai-prod"

# Kill existing session if any
byobu kill-session -t "$SESSION_NAME" 2>/dev/null

# ---------- Window 0: nav2 (single master) ----------
byobu new-session -d -s "$SESSION_NAME" -n "nav2"
byobu send-keys -t "$SESSION_NAME:nav2" \
  "ros2 launch syncai_bringup nav2_bringup_launch.py" Enter

# ---------- Window 1: scan_merger ----------
byobu new-window -t "$SESSION_NAME" -n "scan_merger"
byobu send-keys -t "$SESSION_NAME:scan_merger" \
  "ros2 launch syncai_bringup laser_scan_merger_launch.py" Enter

# ---------- Window 2: api / driver_manager ----------
byobu new-window -t "$SESSION_NAME" -n "api_driver"
byobu send-keys -t "$SESSION_NAME:api_driver" \
  "ros2 launch syncai_robot_api syncai_robot_api.launch.py" Enter
byobu split-window -v -t "$SESSION_NAME:api_driver"
byobu send-keys -t "$SESSION_NAME:api_driver.1" \
  "ros2 launch syncai_driver_manager syncai_driver_manager.launch.py" Enter

# ---------- Window 3: robot_state / bt_plugins ----------
byobu new-window -t "$SESSION_NAME" -n "state_bt"
byobu send-keys -t "$SESSION_NAME:state_bt" \
  "ros2 launch syncai_robot_state syncai_robot_state.launch.py" Enter
byobu split-window -v -t "$SESSION_NAME:state_bt"
byobu send-keys -t "$SESSION_NAME:state_bt.1" \
  "ros2 launch syncai_bt_plugins syncai_bt_plugins_launch.py" Enter

# ---------- Window 4: shell ----------
byobu new-window -t "$SESSION_NAME" -n "shell"

# Go back to nav2 window and attach
byobu select-window -t "$SESSION_NAME:nav2"
byobu attach-session -t "$SESSION_NAME"
