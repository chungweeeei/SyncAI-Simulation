import configparser
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import  PushROSNamespace, SetParameter, Node
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml


def _read_system_ini(data_dir):
    """Read system.ini and return robot_id, initial_pose_x, initial_pose_y."""
    ini_path = os.path.join(data_dir, 'system.ini')
    config = configparser.ConfigParser()
    config.read(ini_path)

    robot_id = config.get('identity', 'robot_id', fallback='')
    initial_pose_x = config.getfloat('spawn', 'initial_pose_x', fallback=0.0)
    initial_pose_y = config.getfloat('spawn', 'initial_pose_y', fallback=0.0)

    return robot_id, initial_pose_x, initial_pose_y


def generate_launch_description():
    bringup_dir = get_package_share_directory('syncai_bringup')

    # Read system.ini at launch-time evaluation
    data_dir_default = os.path.expanduser("~/data")
    robot_id, ini_pose_x, ini_pose_y = _read_system_ini(data_dir_default)

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    initial_pose_x = LaunchConfiguration('initial_pose_x')
    initial_pose_y = LaunchConfiguration('initial_pose_y')
    initial_pose_yaw = LaunchConfiguration('initial_pose_yaw')

    lifecycle_nodes = ['amcl']

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key=namespace,
            param_rewrites={},
            convert_types=True,
        ),
        allow_substs=True,
    )

    # Prepend namespace to frame IDs so TF frames match the namespaced robot
    namespaced_frame_params = {
        'base_frame_id': [namespace, '/base_link'],
        'odom_frame_id': [namespace, '/odom'],
    }

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
        default_value=os.path.join(bringup_dir, 'config', 'amcl_params.yaml'),
        description='Full path to the ROS2 parameters file to use for all launched nodes',
    )

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the amcl node',
    )

    # Initial pose defaults from system.ini [spawn] section
    declare_initial_pose_x_cmd = DeclareLaunchArgument(
        'initial_pose_x',
        default_value=str(ini_pose_x),
        description='Initial pose x position (default from system.ini)',
    )

    declare_initial_pose_y_cmd = DeclareLaunchArgument(
        'initial_pose_y',
        default_value=str(ini_pose_y),
        description='Initial pose y position (default from system.ini)',
    )

    declare_initial_pose_yaw_cmd = DeclareLaunchArgument(
        'initial_pose_yaw',
        default_value='0.0',
        description='Initial pose yaw orientation',
    )

    initial_pose_params = {
        'set_initial_pose': True,
        'initial_pose.x': initial_pose_x,
        'initial_pose.y': initial_pose_y,
        'initial_pose.z': 0.0,
        'initial_pose.yaw': initial_pose_yaw,
    }

    load_nodes = GroupAction(
        actions=[
            PushROSNamespace(namespace),
            SetParameter('use_sim_time', use_sim_time),
            Node(
                package='nav2_amcl',
                executable='amcl',
                name='amcl',
                output='screen',
                parameters=[configured_params, initial_pose_params, namespaced_frame_params],
                arguments=['--ros-args', '--log-level', 'info']
            ),
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_amcl',
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
    ld.add_action(declare_initial_pose_x_cmd)
    ld.add_action(declare_initial_pose_y_cmd)
    ld.add_action(declare_initial_pose_yaw_cmd)

    ld.add_action(load_nodes)

    return ld
