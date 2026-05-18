"""Cartographer pure-localization launch.

Replaces AMCL. Runs `cartographer_node` with a frozen .pbstream so it provides
the map -> <namespace>/odom transform that Nav2 expects. EKF keeps owning
<namespace>/odom -> <namespace>/base_link.

Initial pose is read from ~/data/system.ini ([spawn] initial_pose_x/y/theta)
and pushed to Cartographer via the /<ns>/start_trajectory service after the
node is up. The node is launched with -start_trajectory_with_default_topics=false
so the first trajectory is the one we explicitly start (not an origin-anchored
auto-trajectory).

Cartographer is not a Nav2 lifecycle node, so this launch does not spawn a
lifecycle_manager. The `use_local_lifecycle_manager` argument is accepted
(and ignored) only to keep the include signature compatible with
nav2_bringup_launch.py.
"""
import configparser
import math
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    OpaqueFunction,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushROSNamespace, SetParameter


def _read_system_ini(data_dir):
    """Read system.ini and return (robot_id, x, y, theta)."""
    ini_path = os.path.join(data_dir, 'system.ini')
    config = configparser.ConfigParser()
    config.read(ini_path)
    robot_id = config.get('identity', 'robot_id', fallback='')
    x = config.getfloat('spawn', 'initial_pose_x', fallback=0.0)
    y = config.getfloat('spawn', 'initial_pose_y', fallback=0.0)
    theta = config.getfloat('spawn', 'initial_pose_theta', fallback=0.0)
    return robot_id, x, y, theta


def _build_start_trajectory_call(context, cartographer_config_dir):
    """Compose the ros2 service call that seeds Cartographer's initial pose.

    Quaternion is the 2D yaw convention (roll = pitch = 0):
        qz = sin(theta / 2), qw = cos(theta / 2)
    relative_to_trajectory_id=0 anchors the pose against the frozen map
    loaded from the .pbstream (trajectory 0 is the frozen one).
    """
    namespace = context.launch_configurations['namespace']
    configuration_basename = context.launch_configurations['configuration_basename']
    x = float(context.launch_configurations['initial_pose_x'])
    y = float(context.launch_configurations['initial_pose_y'])
    theta = float(context.launch_configurations['initial_pose_theta'])

    qz = math.sin(theta / 2.0)
    qw = math.cos(theta / 2.0)

    payload = (
        "{{configuration_directory: '{cfg_dir}', "
        "configuration_basename: '{basename}', "
        "use_initial_pose: true, "
        "initial_pose: {{"
        "position: {{x: {x}, y: {y}, z: 0.0}}, "
        "orientation: {{x: 0.0, y: 0.0, z: {qz}, w: {qw}}}"
        "}}, "
        "relative_to_trajectory_id: 0}}"
    ).format(
        cfg_dir=cartographer_config_dir,
        basename=configuration_basename,
        x=x, y=y, qz=qz, qw=qw,
    )

    service = '/{ns}/start_trajectory'.format(ns=namespace)

    return [
        TimerAction(
            period=3.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'service', 'call', service,
                        'cartographer_ros_msgs/srv/StartTrajectory',
                        payload,
                    ],
                    output='screen',
                ),
            ],
        ),
    ]


def generate_launch_description():
    bringup_dir = get_package_share_directory('syncai_bringup')
    cartographer_config_dir = os.path.join(bringup_dir, 'config', 'cartographer')

    robot_id, ini_x, ini_y, ini_theta = _read_system_ini(
        os.path.expanduser('~/data')
    )

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    configuration_basename = LaunchConfiguration('configuration_basename')
    load_state_filename = LaunchConfiguration('load_state_filename')

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

    declare_configuration_basename_cmd = DeclareLaunchArgument(
        'configuration_basename',
        default_value='warehouse_localization.lua',
        description='Cartographer Lua config basename inside config/cartographer/',
    )

    declare_load_state_filename_cmd = DeclareLaunchArgument(
        'load_state_filename',
        default_value='/home/ubuntu/map/warehouse.pbstream',
        description='Full path to the .pbstream file produced by Cartographer SLAM',
    )

    declare_initial_pose_x_cmd = DeclareLaunchArgument(
        'initial_pose_x',
        default_value=str(ini_x),
        description='Initial pose x (default from system.ini [spawn])',
    )

    declare_initial_pose_y_cmd = DeclareLaunchArgument(
        'initial_pose_y',
        default_value=str(ini_y),
        description='Initial pose y (default from system.ini [spawn])',
    )

    declare_initial_pose_theta_cmd = DeclareLaunchArgument(
        'initial_pose_theta',
        default_value=str(ini_theta),
        description='Initial pose yaw in radians (default from system.ini [spawn])',
    )

    # Cartographer is not a lifecycle node; this arg is accepted for parity
    # with the other module launches but is unused.
    declare_use_local_lifecycle_manager_cmd = DeclareLaunchArgument(
        'use_local_lifecycle_manager',
        default_value='true',
        description='Unused for Cartographer (kept for include-signature parity)',
    )

    # Surface the namespace to Lua so it can build namespaced frame IDs
    # (e.g. robot01/base_link, robot01/odom).
    set_robot_namespace_env = SetEnvironmentVariable(
        name='ROBOT_NAMESPACE', value=namespace
    )

    stdout_linebuf_envvar = SetEnvironmentVariable(
        'RCUTILS_LOGGING_BUFFERED_STREAM', '1'
    )

    load_nodes = GroupAction(
        actions=[
            PushROSNamespace(namespace),
            SetParameter('use_sim_time', use_sim_time),
            Node(
                package='cartographer_ros',
                executable='cartographer_node',
                name='cartographer_node',
                output='screen',
                arguments=[
                    '-configuration_directory', cartographer_config_dir,
                    '-configuration_basename', configuration_basename,
                    '-load_state_filename', load_state_filename,
                    '-load_frozen_state',
                    # Don't auto-start a trajectory at origin; we'll start one
                    # explicitly with the initial pose below.
                    '-start_trajectory_with_default_topics=false',
                    '--ros-args', '--log-level', 'info',
                ],
            ),
        ],
    )

    start_initial_trajectory = OpaqueFunction(
        function=_build_start_trajectory_call,
        kwargs={'cartographer_config_dir': cartographer_config_dir},
    )

    ld = LaunchDescription()
    ld.add_action(stdout_linebuf_envvar)
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_configuration_basename_cmd)
    ld.add_action(declare_load_state_filename_cmd)
    ld.add_action(declare_initial_pose_x_cmd)
    ld.add_action(declare_initial_pose_y_cmd)
    ld.add_action(declare_initial_pose_theta_cmd)
    ld.add_action(declare_use_local_lifecycle_manager_cmd)
    ld.add_action(set_robot_namespace_env)
    ld.add_action(load_nodes)
    ld.add_action(start_initial_trajectory)
    return ld
