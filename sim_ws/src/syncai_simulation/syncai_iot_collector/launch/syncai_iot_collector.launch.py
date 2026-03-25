from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='syncai_iot_collector',
            executable='syncai_iot_collector',
            name='iot_collector',
            output='screen',
        ),
    ])
