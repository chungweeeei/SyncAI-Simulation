import configparser
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import EqualsSubstitution, LaunchConfiguration
from launch.substitutions import NotEqualsSubstitution
from launch_ros.actions import PushROSNamespace, SetParameter, Node
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml


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
    map_yaml_file = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')

    lifecycle_nodes = ['map_server']

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
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

    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value='',
        description='Full path to map yaml file to load',
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true',
    )

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(bringup_dir, 'config', 'map_server_params.yaml'),
        description='Full path to the ROS2 parameters file to use for all launched nodes',
    )

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the map server',
    )

    declare_use_respawn_cmd = DeclareLaunchArgument(
        'use_respawn',
        default_value='False',
        description='Whether to respawn if a node crashes. Applied when composition is disabled.',
    )

    load_nodes = GroupAction(
        actions=[
            PushROSNamespace(namespace),
            SetParameter('use_sim_time', use_sim_time),
            Node(
                condition=IfCondition(
                    EqualsSubstitution(LaunchConfiguration('map'), '')
                ),
                package='nav2_map_server',
                executable='map_server',
                name='map_server',
                output='screen',
                parameters=[configured_params],
                arguments=['--ros-args', '--log-level', 'info'],
            ),
            Node(
                condition=IfCondition(
                    NotEqualsSubstitution(LaunchConfiguration('map'), '')
                ),
                package='nav2_map_server',
                executable='map_server',
                name='map_server',
                output='screen',
                parameters=[configured_params, {'yaml_filename': map_yaml_file}],
                arguments=['--ros-args', '--log-level', 'info'],
            ),
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_map_server',
                output='screen',
                arguments=['--ros-args', '--log-level', 'info'],
                parameters=[{'autostart': autostart}, {'node_names': lifecycle_nodes}],
            ),
        ],
    )

    ld = LaunchDescription()

    ld.add_action(stdout_linebuf_envvar)

    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_map_yaml_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(declare_autostart_cmd)

    ld.add_action(load_nodes)

    return ld
