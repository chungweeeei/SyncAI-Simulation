import configparser
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import  PushROSNamespace, SetParameter, Node
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

    data_dir_default = os.environ.get('SYNCAI_DATA_DIR', '/home/ubuntu/data')
    robot_id = _read_system_ini(data_dir_default)

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')

    lifecycle_nodes = ['bt_navigator']

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key=namespace,
            param_rewrites={
                'robot_base_frame': robot_id + '/base_link',
            },
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
        default_value=os.path.join(bringup_dir, 'config', 'bt_navigator_params.yaml'),
        description='Full path to the ROS2 parameters file to use',
    )

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the bt navigator',
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
                package='nav2_bt_navigator',
                executable='bt_navigator',
                name='bt_navigator',
                output='screen',
                parameters=[configured_params],
                arguments=['--ros-args', '--log-level', 'info']
            ),
            Node(
                condition=IfCondition(LaunchConfiguration('use_local_lifecycle_manager')),
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_bt_navigator',
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

    ld.add_action(declare_use_local_lifecycle_manager_cmd)

    ld.add_action(load_nodes)

    return ld
