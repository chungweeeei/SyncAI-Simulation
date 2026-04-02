import os
import configparser

from launch import LaunchDescription
from launch.actions import GroupAction
from launch_ros.actions import PushRosNamespace, Node


def generate_launch_description():

    data_dir = os.path.expanduser("~/data")
    config = configparser.ConfigParser()
    config.read(os.path.join(data_dir, "system.ini"))
    robot_id = config.get("identity", "robot_id", fallback="robot01")

    agent_node = Node(
        package='syncai_agent',
        executable='syncai_agent',
        name='syncai_agent',
        output='screen',
    )

    group = GroupAction([
        PushRosNamespace(robot_id),
        agent_node,
    ])

    return LaunchDescription([group])
