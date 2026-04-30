from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('host', default_value='0.0.0.0'),
        DeclareLaunchArgument('port', default_value='5020'),
        DeclareLaunchArgument('unit_id', default_value='1'),
        DeclareLaunchArgument('config_file', default_value=''),

        Node(
            package='syncai_modbus_server',
            executable='modbus_server',
            name='modbus_server',
            parameters=[{
                'host': LaunchConfiguration('host'),
                'port': LaunchConfiguration('port'),
                'unit_id': LaunchConfiguration('unit_id'),
                'config_file': LaunchConfiguration('config_file'),
            }],
            output='screen',
        ),
    ])
