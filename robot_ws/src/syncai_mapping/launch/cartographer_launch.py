import configparser
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushROSNamespace, SetParameter


def _read_robot_id(data_dir):
    ini_path = os.path.join(data_dir, 'system.ini')
    config = configparser.ConfigParser()
    config.read(ini_path)
    return config.get('identity', 'robot_id', fallback='')


def _materialize_lua_config(context, *args, **kwargs):
    # cartographer_node's -configuration_directory takes a directory, so we
    # can't use nav2_common.launch.ReplaceString (single-file output). Read
    # the packaged lua, substitute <robot_namespace>, and write it to a
    # per-robot temp dir before pointing cartographer at it.
    namespace = context.perform_substitution(LaunchConfiguration('namespace'))
    config_basename = context.perform_substitution(LaunchConfiguration('config_basename'))

    pkg_share = get_package_share_directory('syncai_mapping')
    src_path = os.path.join(pkg_share, 'config', config_basename)

    with open(src_path, 'r') as f:
        content = f.read()
    content = content.replace('<robot_namespace>', namespace)

    safe_ns = namespace.replace('/', '_') or 'default'
    out_dir = os.path.join('/tmp', f'syncai_cartographer_{safe_ns}')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, config_basename), 'w') as f:
        f.write(content)

    return [
        GroupAction(actions=[
            PushROSNamespace(LaunchConfiguration('namespace')),
            SetParameter('use_sim_time', LaunchConfiguration('use_sim_time')),
            Node(
                package='cartographer_ros',
                executable='cartographer_node',
                name='syncai_mapping_node',
                output='screen',
                arguments=[
                    '-configuration_directory', out_dir,
                    '-configuration_basename', config_basename,
                ],
            ),
            Node(
                package='cartographer_ros',
                executable='cartographer_occupancy_grid_node',
                name='syncai_occupancy_grid_node',
                output='screen',
                parameters=[{
                    'resolution': LaunchConfiguration('resolution'),
                    'publish_period_sec': LaunchConfiguration('publish_period_sec'),
                }],
                remappings=[('map', 'mapping')],
            ),
        ]),
    ]


def generate_launch_description():
    robot_id = _read_robot_id(os.path.expanduser('~/data'))

    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value=robot_id,
        description='Top-level namespace (default: robot_id from system.ini)',
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true',
    )

    declare_config_basename_cmd = DeclareLaunchArgument(
        'config_basename',
        default_value='cartographer_2d.lua',
        description='Cartographer Lua config filename in syncai_mapping/config',
    )

    declare_resolution_cmd = DeclareLaunchArgument(
        'resolution',
        default_value='0.05',
        description='Occupancy grid resolution (m/pixel)',
    )

    declare_publish_period_cmd = DeclareLaunchArgument(
        'publish_period_sec',
        default_value='1.0',
        description='Occupancy grid publish period (sec)',
    )

    stdout_linebuf_envvar = SetEnvironmentVariable(
        'RCUTILS_LOGGING_BUFFERED_STREAM', '1'
    )

    ld = LaunchDescription()
    ld.add_action(stdout_linebuf_envvar)
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_config_basename_cmd)
    ld.add_action(declare_resolution_cmd)
    ld.add_action(declare_publish_period_cmd)
    ld.add_action(OpaqueFunction(function=_materialize_lua_config))
    return ld
