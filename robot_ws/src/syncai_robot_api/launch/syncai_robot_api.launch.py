import configparser
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushROSNamespace, Node


def _read_system_ini(data_dir):
    ini_path = os.path.join(data_dir, 'system.ini')
    config = configparser.ConfigParser()
    config.read(ini_path)
    robot_id = config.get('identity', 'robot_id', fallback='robot01')
    robot_name = config.get('identity', 'robot_name', fallback=robot_id)
    return robot_id, robot_name


def generate_launch_description():
    data_dir_default = os.path.expanduser("~/data")
    robot_id, _ = _read_system_ini(data_dir_default)

    namespace = LaunchConfiguration('namespace')

    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value=robot_id,
        description='Top-level namespace (default: robot_id from system.ini)',
    )

    load_nodes = GroupAction(
        actions=[
            PushROSNamespace(namespace),
            Node(
                package='syncai_robot_api',
                executable='syncai_robot_api',
                name='syncai_robot_api',
                output='screen',
                parameters=[],
            ),
        ],
    )

    ld = LaunchDescription()
    ld.add_action(declare_namespace_cmd)
    ld.add_action(load_nodes)
    return ld
