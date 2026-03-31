import configparser
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushROSNamespace, SetParameter, Node
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import ReplaceString, RewrittenYaml


def _read_system_ini(data_dir):
    """Read system.ini and return robot_id."""
    ini_path = os.path.join(data_dir, 'system.ini')
    config = configparser.ConfigParser()
    config.read(ini_path)
    return config.get('identity', 'robot_id', fallback='')


def generate_launch_description():
    bringup_dir = get_package_share_directory('syncai_bringup')

    # Read system.ini at launch-time evaluation
    robot_id = _read_system_ini(os.path.expanduser("~/data"))

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')

    lifecycle_nodes = ['filter_mask_server', 'costmap_filter_info_server']

    replaced_params_file = ReplaceString(
        source_file=params_file,
        replacements={'<robot_namespace>': namespace},
    )

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=replaced_params_file,
            root_key=namespace,
            param_rewrites={},
            convert_types=True,
        ),
        allow_substs=True,
    )

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

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(bringup_dir, 'config', 'costmap_filter_params.yaml'),
        description='Full path to the costmap filter parameters file',
    )

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the costmap filter nodes',
    )

    load_nodes = GroupAction(
        actions=[
            PushROSNamespace(namespace),
            SetParameter('use_sim_time', use_sim_time),
            Node(
                package='nav2_map_server',
                executable='map_server',
                name='filter_mask_server',
                output='screen',
                parameters=[configured_params],
                remappings=[('map', 'filter_mask')],
                arguments=['--ros-args', '--log-level', 'info'],
            ),
            Node(
                package='nav2_map_server',
                executable='costmap_filter_info_server',
                name='costmap_filter_info_server',
                output='screen',
                parameters=[configured_params],
                arguments=['--ros-args', '--log-level', 'info'],
            ),
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_costmap_filter',
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
    ld.add_action(declare_params_file_cmd)
    ld.add_action(declare_autostart_cmd)

    ld.add_action(load_nodes)

    return ld
