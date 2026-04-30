from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="syncai_wms",
                executable="syncai_wms",
                name="syncai_wms",
                output="screen",
            ),
        ]
    )
