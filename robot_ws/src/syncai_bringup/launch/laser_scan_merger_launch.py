import configparser
import os
import tempfile

import yaml
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushROSNamespace, SetParameter, Node


def _read_system_ini(data_dir):
    """Read system.ini and return robot_id."""
    ini_path = os.path.join(data_dir, 'system.ini')
    config = configparser.ConfigParser()
    config.read(ini_path)
    return config.get('identity', 'robot_id', fallback='')


def _generate_namespaced_params(params_file, robot_id):
    """Rewrite frame IDs and wrap the node-param blocks under the robot
    namespace so the yaml keys match the fully-qualified node names
    (/<robot_id>/ros2_laser_scan_merger, /<robot_id>/pointcloud_to_laserscan).
    """
    with open(params_file, 'r') as f:
        params = yaml.safe_load(f)

    # Use the dedicated `scan` frame (chassis-local z=0.25) instead of
    # base_link. Sim's IsaacComputeOdometry-based publisher reports base_link
    # at odom z=0; nav2's voxel layer then rejects sensor origins at exactly
    # z=origin_z=0 on float jitter and silently drops every raytrace. The
    # `scan` frame sits ~0.25 m above base_link (published as a static TF by
    # the `base_link_to_scan_tf` Node in this launch), well within the voxel
    # layer's z range, so the warning goes away.
    merger = params.get('ros2_laser_scan_merger', {}).get('ros__parameters', {})
    if 'pointCloutFrameId' in merger:
        merger['pointCloutFrameId'] = robot_id + '/scan'

    p2l = params.get('pointcloud_to_laserscan', {}).get('ros__parameters', {})
    if 'target_frame' in p2l:
        p2l['target_frame'] = robot_id + '/scan'

    namespaced = {robot_id: {k: v for k, v in params.items() if k != '/**'}}
    if '/**' in params:
        namespaced['/**'] = params['/**']

    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.yaml', prefix='laser_scan_merger_', delete=False
    )
    yaml.dump(namespaced, tmp, default_flow_style=False)
    tmp.close()
    return tmp.name


def generate_launch_description():
    bringup_dir = get_package_share_directory('syncai_bringup')

    data_dir_default = os.path.expanduser("~/data")
    robot_id = _read_system_ini(data_dir_default)

    default_params_file = os.path.join(
        bringup_dir, 'config', 'laser_scan_merger_params.yaml'
    )
    namespaced_params_file = _generate_namespaced_params(
        default_params_file, robot_id
    )

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')

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
        description='Use simulation (Isaac Sim) clock if true',
    )

    load_nodes = GroupAction(
        actions=[
            PushROSNamespace(namespace),
            SetParameter('use_sim_time', use_sim_time),
            Node(
                package='ros2_laser_scan_merger',
                executable='ros2_laser_scan_merger',
                name='ros2_laser_scan_merger',
                output='screen',
                parameters=[namespaced_params_file],
                arguments=['--ros-args', '--log-level', 'info'],
            ),
            Node(
                package='pointcloud_to_laserscan',
                executable='pointcloud_to_laserscan_node',
                name='pointcloud_to_laserscan',
                output='screen',
                parameters=[namespaced_params_file],
                arguments=['--ros-args', '--log-level', 'info'],
            ),
        ],
    )

    # Static TF: <ns>/base_link -> <ns>/scan, z=+0.25.
    # The merger output (pointCloutFrameId) and pointcloud_to_laserscan's
    # target_frame are stamped `<ns>/scan` (rewritten in
    # _generate_namespaced_params above), but Omniverse's tf_publisher only
    # publishes `<ns>/base_link -> <ns>/{scan_front,scan_rear}`, leaving
    # `<ns>/scan` orphaned -- AMCL's message filter then drops every scan
    # because it can't resolve the sensor frame. Publishing the static
    # transform here closes the gap. z=+0.25 lifts the sensor origin clear
    # of nav2's voxel_layer origin_z=0.0 (avoids float-jitter raytrace drops).
    #
    # Kept OUTSIDE the GroupAction above: PushROSNamespace would otherwise
    # remap /tf_static to /<ns>/tf_static, fragmenting the global TF tree
    # that AMCL / nav2 subscribe to.
    # Frame ids use list-substitution against `namespace` (a LaunchConfiguration)
    # so they resolve to whatever was actually passed at launch -- mirroring how
    # PushROSNamespace(namespace) is used inside load_nodes. Inlining the
    # launch-time `robot_id` Python str instead would freeze the value at
    # generate_launch_description time and miss any --namespace CLI override
    # (and emit `/base_link` if system.ini is missing).
    base_link_to_scan_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_to_scan_tf',
        output='screen',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0.25',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', [namespace, '/base_link'],
            '--child-frame-id', [namespace, '/scan'],
        ],
        parameters=[{'use_sim_time': True}],
    )

    ld = LaunchDescription()
    ld.add_action(stdout_linebuf_envvar)
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(load_nodes)
    ld.add_action(base_link_to_scan_tf)
    return ld
