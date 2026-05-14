"""
Nav2 prod bringup: include all per-module launches with their local
lifecycle_managers disabled, then add a single master lifecycle_manager
that drives the full Nav2 stack in the correct startup order.

Each per-module launch supports a `use_local_lifecycle_manager` arg
(default true). Passing false here makes the per-module lifecycle_manager
Node skip itself, leaving only the server Node(s).

Result vs. dev profile: ~9 lifecycle_manager processes collapse into 1,
saving DDS participants and giving a deterministic startup order.
"""
import configparser
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushROSNamespace


def _read_robot_id(data_dir):
    ini_path = os.path.join(data_dir, 'system.ini')
    config = configparser.ConfigParser()
    config.read(ini_path)
    return config.get('identity', 'robot_id', fallback='')


# Nav2 startup order — lifecycle_manager will configure/activate in this order
NAV2_LIFECYCLE_NODES = [
    'map_server',
    'filter_mask_server',
    'costmap_filter_info_server',
    'amcl',
    'controller_server',
    'planner_server',
    'smoother_server',
    'behavior_server',
    'bt_navigator',
    'velocity_smoother',
    'docking_server',
]

# Module launches to include (lifecycle_manager skipped via launch arg)
NAV2_MODULE_LAUNCHES = [
    'map_server_launch.py',
    'costmap_filter_launch.py',
    'amcl_launch.py',
    'controller_launch.py',
    'planner_launch.py',
    'path_smoother_launch.py',
    'behavior_launch.py',
    'bt_navigator_launch.py',
    'velocity_smoother_launch.py',
    'docking_launch.py',
]


def generate_launch_description():
    bringup_dir = get_package_share_directory('syncai_bringup')
    launch_dir = os.path.join(bringup_dir, 'launch')

    robot_id = _read_robot_id(os.path.expanduser('~/data'))

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')

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

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Auto-activate the Nav2 stack via the master lifecycle_manager',
    )

    forwarded_args = [
        ('namespace', namespace),
        ('use_sim_time', use_sim_time),
        ('use_local_lifecycle_manager', 'false'),
    ]

    # Each include is wrapped in a scoped GroupAction so the per-module
    # `params_file` LaunchConfiguration default does not leak out and clobber
    # the next include's params_file (e.g., docking_server picking up
    # map_server_params.yaml).
    module_includes = [
        GroupAction(
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(os.path.join(launch_dir, f)),
                    launch_arguments=forwarded_args,
                ),
            ],
        )
        for f in NAV2_MODULE_LAUNCHES
    ]

    master_lifecycle_manager = GroupAction(
        actions=[
            PushROSNamespace(namespace),
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_navigation',
                output='screen',
                arguments=['--ros-args', '--log-level', 'info'],
                parameters=[{
                    'autostart': autostart,
                    'node_names': NAV2_LIFECYCLE_NODES,
                    'bond_timeout': 4.0,
                }],
            ),
        ],
    )

    ld = LaunchDescription()
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_autostart_cmd)
    for include in module_includes:
        ld.add_action(include)
    ld.add_action(master_lifecycle_manager)
    return ld
