#!/bin/bash
# =============================================================================
# SyncAI Robot Byobu Session
# Usage: bash byobu_session.sh
# =============================================================================

SESSION_NAME="syncai"

# Kill existing session if any
byobu kill-session -t "$SESSION_NAME" 2>/dev/null

# ---------- Window 0: map_server / amcl ----------
byobu new-session -d -s "$SESSION_NAME" -n "localization"
byobu send-keys -t "$SESSION_NAME:localization" \
  "ros2 launch syncai_bringup map_server_launch.py" Enter
byobu split-window -v -t "$SESSION_NAME:localization"
byobu send-keys -t "$SESSION_NAME:localization.1" \
  "ros2 launch syncai_bringup amcl_launch.py" Enter

# ---------- Window 1: planner / controller ----------
byobu new-window -t "$SESSION_NAME" -n "plan_ctrl"
byobu send-keys -t "$SESSION_NAME:plan_ctrl" \
  "ros2 launch syncai_bringup planner_launch.py" Enter
byobu split-window -v -t "$SESSION_NAME:plan_ctrl"
byobu send-keys -t "$SESSION_NAME:plan_ctrl.1" \
  "ros2 launch syncai_bringup controller_launch.py" Enter

# ---------- Window 2: bt_navigator / smoother ----------
byobu new-window -t "$SESSION_NAME" -n "bt_smooth"
byobu send-keys -t "$SESSION_NAME:bt_smooth" \
  "ros2 launch syncai_bringup bt_navigator_launch.py" Enter
byobu split-window -v -t "$SESSION_NAME:bt_smooth"
byobu send-keys -t "$SESSION_NAME:bt_smooth.1" \
  "ros2 launch syncai_bringup smoother_launch.py" Enter

# ---------- Window 3: behavior / velocity_smoother ----------
byobu new-window -t "$SESSION_NAME" -n "behav_vel"
byobu send-keys -t "$SESSION_NAME:behav_vel" \
  "ros2 launch syncai_bringup behavior_launch.py" Enter
byobu split-window -v -t "$SESSION_NAME:behav_vel"
byobu send-keys -t "$SESSION_NAME:behav_vel.1" \
  "ros2 launch syncai_bringup velocity_smoother_launch.py" Enter

# ---------- Window 4: robot_api / driver_manager ----------
byobu new-window -t "$SESSION_NAME" -n "api_driver"
byobu send-keys -t "$SESSION_NAME:api_driver" \
  "ros2 launch syncai_robot_api syncai_robot_api.launch.py" Enter
byobu split-window -v -t "$SESSION_NAME:api_driver"
byobu send-keys -t "$SESSION_NAME:api_driver.1" \
  "ros2 launch syncai_driver_manager syncai_driver_manager.launch.py" Enter

# ---------- Window 5: robot_state / shell ----------
byobu new-window -t "$SESSION_NAME" -n "state_shell"
byobu send-keys -t "$SESSION_NAME:state_shell" \
  "ros2 launch syncai_robot_state syncai_robot_state.launch.py" Enter
byobu split-window -v -t "$SESSION_NAME:state_shell"
byobu send-keys -t "$SESSION_NAME:state_shell.1" \
  "" Enter

# Go back to window 0 and attach
byobu select-window -t "$SESSION_NAME:localization"
byobu attach-session -t "$SESSION_NAME"
