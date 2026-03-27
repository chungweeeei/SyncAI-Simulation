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
    ini_path = os.path.join(data_dir, 'system.ini')
    config = configparser.ConfigParser()
    config.read(ini_path)
    return config.get('identity', 'robot_id', fallback='')


def generate_launch_description():
    bringup_dir = get_package_share_directory('syncai_bringup')

    data_dir_default = os.path.expanduser("~/data")
    robot_id = _read_system_ini(data_dir_default)

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')

    # Step 1: Replace <robot_namespace> placeholders (for frame IDs)
    replaced_params_file = ReplaceString(
        source_file=params_file,
        replacements={'<robot_namespace>': namespace},
    )

    # Step 2: Wrap YAML under namespace key so it matches
    #         /<namespace>/ekf_filter_node when using PushROSNamespace
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
        default_value=os.path.join(bringup_dir, 'config', 'ekf_params.yaml'),
        description='Full path to the EKF parameters file',
    )

    load_nodes = GroupAction(
        actions=[
            PushROSNamespace(namespace),
            SetParameter('use_sim_time', use_sim_time),
            Node(
                package='robot_localization',
                executable='ekf_node',
                name='ekf_filter_node',
                output='screen',
                parameters=[configured_params],
                remappings=[
                    ('odometry/filtered', 'ekf_odom'),
                ],
                arguments=['--ros-args', '--log-level', 'info'],
            ),
        ],
    )

    ld = LaunchDescription()

    ld.add_action(stdout_linebuf_envvar)
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(load_nodes)

    return ld
