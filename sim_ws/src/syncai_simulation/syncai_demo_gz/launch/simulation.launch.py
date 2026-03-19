import os
import glob
import configparser

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    default_world = PathJoinSubstitution([
        FindPackageShare("syncai_demo_gz"),
        "worlds",
        "dp1f.world"
    ])

    actions = [
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
            namespace=robot_id,
            arguments=[
                "-file", os.path.join(DATA_DIR, robot_id, "model.sdf"),
                "-name", robot_id,
                "-x", x, 
                "-y", y,
                "-z", z,
            ]
        ))

        # ROS <-> Gazebo bridge
        actions.append(Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            namespace=robot_id,
            arguments=[
                f"/{robot_id}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
                f'/{robot_id}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                f'/{robot_id}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
            ],
            output="screen"
        ))

        actions.append(Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0.0', '0.0', '0.12', '0', '0', '0', f'{robot_id}/base_link', f'{robot_id}/laser'],
            output='screen'
        ))

    return LaunchDescription(actions)