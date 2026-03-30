import configparser
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushROSNamespace, SetParameter, Node


def _read_system_ini(data_dir):
    ini_path = os.path.join(data_dir, 'system.ini')
    config = configparser.ConfigParser()
    config.read(ini_path)
    return config.get('identity', 'robot_id', fallback='')


def generate_launch_description():
    pkg_dir = get_package_share_directory('syncai_bt_plugins')

    data_dir_default = os.path.expanduser("~/data")
    robot_id = _read_system_ini(data_dir_default)

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')

    door_control_bt_xml = os.path.join(pkg_dir, 'config', 'door_control.xml')
    charging_bt_xml = os.path.join(pkg_dir, 'config', 'charging.xml')
    navigate_through_door_bt_xml = os.path.join(pkg_dir, 'config', 'navigate_through_door.xml')

    stdout_linebuf_envvar = SetEnvironmentVariable(
        'RCUTILS_LOGGING_BUFFERED_STREAM', '1'
    )

    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value=robot_id,
        description='Top-level namespace (default: robot_id from system.ini)',
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true',
    )

    load_nodes = GroupAction(
        actions=[
            PushROSNamespace(namespace),
            SetParameter('use_sim_time', use_sim_time),
            Node(
                package='syncai_bt_plugins',
                executable='door_control_server',
                name='door_control_server',
                output='screen',
                parameters=[{'bt_xml_file': door_control_bt_xml}],
                arguments=['--ros-args', '--log-level', 'info'],
            ),
            Node(
                package='syncai_bt_plugins',
                executable='charging_server',
                name='charging_server',
                output='screen',
                parameters=[{'bt_xml_file': charging_bt_xml}],
                arguments=['--ros-args', '--log-level', 'info'],
            ),
            Node(
                package='syncai_bt_plugins',
                executable='navigate_through_door_server',
                name='navigate_through_door_server',
                output='screen',
                parameters=[{'bt_xml_file': navigate_through_door_bt_xml}],
                arguments=['--ros-args', '--log-level', 'info'],
            ),
        ],
    )

    ld = LaunchDescription()

    ld.add_action(stdout_linebuf_envvar)
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(load_nodes)

    return ld
