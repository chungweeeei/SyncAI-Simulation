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

    return LaunchDescription([
        DeclareLaunchArgument(
            "battery_initial_level", 
            default_value="100.0",
            description="Initial battery percentage (0-100)"
        ),
        DeclareLaunchArgument(
            "battery_discharge_rate",
            default_value="0.01",
            description="Battery discharge rate in percentage per second"
        ),
        DeclareLaunchArgument(
            "battery_charge_rate",
            default_value="0.5",
            description="Battery charge rate in percentage per second"
        ),
        DeclareLaunchArgument(
            "battery_publish_rate",
            default_value="1.0",
            description="Rate at which battery status is published (Hz)"
        ),
        DeclareLaunchArgument(
            "robot_frame_id",
            default_value=f"{robot_id}/base_link",
            description="Frame ID of the robot"
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation clock"
        ),

        Node(
            package="syncai_driver_manager",
            executable="syncai_driver_manager",
            name="syncai_driver_manager",
            output="screen",
            namespace=f"{robot_id}",
            parameters=[
                {"battery_initial_level": LaunchConfiguration("battery_initial_level")},
                {"battery_discharge_rate": LaunchConfiguration("battery_discharge_rate")},
                {"battery_charge_rate": LaunchConfiguration("battery_charge_rate")},
                {"battery_publish_rate": LaunchConfiguration("battery_publish_rate")},
                {"robot_frame_id": LaunchConfiguration("robot_frame_id")},
                {"use_sim_time": LaunchConfiguration("use_sim_time")},
            ]
        )
    ])