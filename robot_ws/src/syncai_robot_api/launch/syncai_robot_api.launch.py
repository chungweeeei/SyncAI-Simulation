from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='syncai_robot_api',
            executable='syncai_robot_api',
            name='syncai_robot_api',
            output='screen',
        ),
    ])
