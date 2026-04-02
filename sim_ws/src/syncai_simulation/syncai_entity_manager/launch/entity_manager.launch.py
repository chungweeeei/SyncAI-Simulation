from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    entity_manager_node = Node(
        package='syncai_entity_manager',
        executable='entity_manager_node',
        name='entity_manager',
        output='screen',
        parameters=[],
    )

    return LaunchDescription([
        entity_manager_node,
    ])
