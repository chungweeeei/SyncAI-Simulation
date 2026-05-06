import configparser
import os
import tempfile

import yaml
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushROSNamespace, SetParameter, Node


def _read_system_ini(data_dir):
    """Read system.ini and return robot_id."""
    ini_path = os.path.join(data_dir, 'system.ini')
    config = configparser.ConfigParser()
    config.read(ini_path)
    return config.get('identity', 'robot_id', fallback='')


def _generate_namespaced_params(params_file, robot_id):
    """Read yaml, inject namespace into frame IDs, write to temp file."""
    with open(params_file, 'r') as f:
        params = yaml.safe_load(f)

    # Inject namespace into local_costmap frame IDs and scan topic
    if 'local_costmap' in params:
        costmap = params['local_costmap']['local_costmap']['ros__parameters']
        costmap['global_frame'] = robot_id + '/odom'
        costmap['robot_base_frame'] = robot_id + '/base_link'
        # Fix keepout_filter topic: resolve to absolute namespace path
        keepout = costmap.get('keepout_filter', {})
        if 'filter_info_topic' in keepout:
            keepout['filter_info_topic'] = '/' + robot_id + '/costmap_filter_info'

        # Fix speed_filter topic: resolve to absolute namespace path
        speed = costmap.get('speed_filter', {})
        if 'filter_info_topic' in speed:
            speed['filter_info_topic'] = '/' + robot_id + '/speed_filter_info'
        speed['speed_limit_topic'] = '/' + robot_id + '/speed_limit'

        # Fix scan topic: sub-node resolves relative 'scan' to /<ns>/local_costmap/scan
        for layer_key in ['voxel_layer', 'obstacle_layer']:
            layer = costmap.get(layer_key, {})
            for src_name in layer.get('observation_sources', '').split():
                src = layer.get(src_name, {})
                if src.get('topic') == 'scan':
                    src['topic'] = '/' + robot_id + '/scan'

    # Fix FollowPath speed_limit_topic: RPPC subscribes on controller_server namespace,
    # must match the absolute topic that SpeedFilter publishes on.
    controller = params.get('controller_server', {}).get('ros__parameters', {})
    follow_path = controller.get('FollowPath', {})
    if follow_path:
        follow_path['speed_limit_topic'] = '/' + robot_id + '/speed_limit'

    # Wrap under namespace so the namespaced node can find its params
    namespaced_params = {robot_id: params}

    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.yaml', prefix='controller_', delete=False
    )
    yaml.dump(namespaced_params, tmp, default_flow_style=False)
    tmp.close()
    return tmp.name


def generate_launch_description():
    bringup_dir = get_package_share_directory('syncai_bringup')

    data_dir_default = os.path.expanduser("~/data")
    robot_id = _read_system_ini(data_dir_default)

    default_params_file = os.path.join(bringup_dir, 'config', 'controller_params.yaml')
    namespaced_params_file = _generate_namespaced_params(default_params_file, robot_id)

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')

    lifecycle_nodes = ['controller_server']

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

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the controller server',
    )

    declare_use_local_lifecycle_manager_cmd = DeclareLaunchArgument(
        'use_local_lifecycle_manager',
        default_value='true',
        description='Spawn a local lifecycle_manager (false when nav2_bringup_launch manages it globally)',
    )

    load_nodes = GroupAction(
        actions=[
            PushROSNamespace(namespace),
            SetParameter('use_sim_time', use_sim_time),
            Node(
                package='nav2_controller',
                executable='controller_server',
                output='screen',
                parameters=[namespaced_params_file],
                arguments=['--ros-args', '--log-level', 'info']
            ),
            Node(
                condition=IfCondition(LaunchConfiguration('use_local_lifecycle_manager')),
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_controller',
                output='screen',
                arguments=['--ros-args', '--log-level', 'info'],
                parameters=[{'autostart': autostart}, {'node_names': lifecycle_nodes}],
            ),
        ],
    )

    ld = LaunchDescription()

    ld.add_action(stdout_linebuf_envvar)
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_autostart_cmd)

    ld.add_action(declare_use_local_lifecycle_manager_cmd)

    ld.add_action(load_nodes)

    return ld
