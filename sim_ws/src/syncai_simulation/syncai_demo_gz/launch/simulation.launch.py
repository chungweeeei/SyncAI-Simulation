import os
import glob
import configparser
import yaml

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_prefix, get_package_share_directory

def generate_launch_description():

    default_world = PathJoinSubstitution([
        FindPackageShare("syncai_demo_gz"),
        "worlds",
        "dp1f.world"
    ])

    # Set GZ_SIM_SYSTEM_PLUGIN_PATH so Gazebo can find our custom plugins
    plugin_dir = os.path.join(get_package_prefix("syncai_demo_gz"), "lib", "syncai_demo_gz")
    gz_plugin_path = os.environ.get("GZ_SIM_SYSTEM_PLUGIN_PATH", "")
    if gz_plugin_path:
        plugin_dir = plugin_dir + ":" + gz_plugin_path

    # Set GZ_SIM_RESOURCE_PATH so Gazebo can resolve package:// URIs for models
    share_dir = os.path.join(get_package_prefix("syncai_demo_gz"), "share")
    gz_resource_path = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    if gz_resource_path:
        share_dir = share_dir + ":" + gz_resource_path

    actions = [
        SetEnvironmentVariable("GZ_SIM_SYSTEM_PLUGIN_PATH", plugin_dir),
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", share_dir),
        DeclareLaunchArgument("world", default_value=default_world),
        DeclareLaunchArgument("gui", default_value="true"),
        DeclareLaunchArgument("headless", default_value="false"),
        SetParameter(name="use_sim_time", value=True),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare("ros_gz_sim"), "/launch/gz_sim.launch.py"
            ]),
            launch_arguments={
                "gz_args": ["-r -v 4 ", LaunchConfiguration("world")],
                "on_exit_shutdown": "true",
            }.items(),
        )
    ]

    bridge_topics = [
        # Camera topic
        "/camera@sensor_msgs/msg/Image[gz.msgs.Image",
        # Global topics
        "/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
        "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"
    ]

    # Load IoT device config from syncai_iot_collector package
    iot_config_path = os.path.join(
        get_package_share_directory("syncai_iot_collector"), "config", "iot_devices.yaml"
    )
    with open(iot_config_path, "r") as f:
        iot_config = yaml.safe_load(f)

    # Spawn and bridge IoT devices from config
    for device in iot_config.get("devices", []):
        device_id = device["id"]
        device_type = device["type"]

        if device_type == "door":
            # Doors are spawned dynamically by launch file
            pose = device.get("pose", [0, 0, 0, 0, 0, 0])
            door_model_path = PathJoinSubstitution([
                FindPackageShare("syncai_demo_gz"),
                "models", "door", "model.sdf"
            ])
            actions.append(Node(
                package="ros_gz_sim",
                executable="create",
                name=f"spawn_{device_id}",
                arguments=[
                    "-file", door_model_path,
                    "-name", device_id,
                    "-x", str(pose[0]),
                    "-y", str(pose[1]),
                    "-z", str(pose[2]),
                ],
                output="screen"
            ))

        # Bridge topics for all device types (door, alarm)
        bridge_topics.extend([
            f"/{device_type}/{device_id}/cmd_topic@std_msgs/msg/Bool]gz.msgs.Boolean",
            f"/{device_type}/{device_id}/state@std_msgs/msg/String[gz.msgs.StringMsg",
        ])


    DATA_DIR = os.path.expanduser("~/data")
    for config_file in glob.glob(os.path.join(DATA_DIR, "*/system.ini")):
        cfg = configparser.ConfigParser()
        cfg.read(config_file)

        robot_id = cfg["identity"]["robot_id"]
        x = cfg["spawn"]["initial_pose_x"]
        y = cfg["spawn"]["initial_pose_y"]
        z = cfg["spawn"]["initial_pose_z"]

        print(f"Spawning {robot_id} at ({x}, {y}, {z})")

        # Spawn into Gazebo
        actions.append(Node(
            package="ros_gz_sim",
            executable="create",
            name=f"spawn_{robot_id}",
            namespace=robot_id,
            arguments=[
                "-file", os.path.join(DATA_DIR, robot_id, "model.sdf"),
                "-name", robot_id,
                "-x", x,
                "-y", y,
                "-z", z,
            ]
        ))

        bridge_topics.extend([
            f"/{robot_id}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            f"/{robot_id}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            f"/{robot_id}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            f"/{robot_id}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            f"/{robot_id}/alert@std_msgs/msg/Bool]gz.msgs.Boolean",
        ])

        actions.append(Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0.0', '0.0', '0.12', '0', '0', '0', f'{robot_id}/base_link', f'{robot_id}/laser'],
            output='screen'
        ))

        actions.append(Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', f'{robot_id}/base_link', f'{robot_id}/imu'],
            output='screen'
        ))

    # Create a single ROS <-> Gazebo bridge node for all topics
    actions.append(Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=bridge_topics,
        output="screen"
    ))

    return LaunchDescription(actions)