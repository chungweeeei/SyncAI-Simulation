import os
import configparser

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    config_path = os.path.join(os.path.expanduser("~/data"), "system.ini")
    cfg = configparser.ConfigParser()
    cfg.read(config_path)

    robot_id = cfg["identity"]["robot_id"]
    robot_name = cfg["identity"]["robot_name"]
    map_name = cfg["spawn"]["map"]

    return LaunchDescription([

        DeclareLaunchArgument(
            "model",
            default_value="AMR",
            description="Type of robot model (e.g., AMR, AGV)"
        ),

        DeclareLaunchArgument(
            "map_name",
            default_value=map_name,
            description="Name of the map to use for navigation"
        ),

        DeclareLaunchArgument(
            'publish_rate',
            default_value='1.0',
            description='Robot state publish rate (Hz)'
        ),

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock'
        ),
        
        Node(
            package="syncai_robot_state",
            executable="syncai_robot_state",
            name="syncai_robot_state",
            namespace=robot_id,
            output="screen",
            parameters=[{
                "robot_id": robot_id,
                "robot_name": robot_name,
                "model": LaunchConfiguration("model"),
                "map_name": LaunchConfiguration("map_name"),
                "publish_rate": LaunchConfiguration("publish_rate"),
                "use_sim_time": LaunchConfiguration("use_sim_time")
            }]
        )
    ])