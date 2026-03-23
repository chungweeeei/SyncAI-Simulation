#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash

# Source workspace if built
if [ -f /home/ubuntu/robot_ws/install/setup.bash ]; then
    source /home/ubuntu/robot_ws/install/setup.bash
fi

exec "$@"
