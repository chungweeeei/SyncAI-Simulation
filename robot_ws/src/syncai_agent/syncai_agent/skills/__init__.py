from syncai_agent.skills.navigation import navigate_to_pose, navigate_with_alert
from syncai_agent.skills.door import control_door
from syncai_agent.skills.charging import charge
from syncai_agent.skills.robot_state import get_robot_state
from syncai_agent.skills.battery import set_battery_level
from syncai_agent.skills import ros_cli


def build_skills(gateway, modbus_gateway, get_state_fn) -> dict:
    return {
        # High-level programmatic skills
        "navigate_to_pose": lambda x, y, yaw: navigate_to_pose(gateway, x, y, yaw),
        "navigate_with_alert": lambda x, y, yaw: navigate_with_alert(gateway, x, y, yaw),
        "control_door": lambda cmd_topic, open=True, timeout_sec=10.0: control_door(
            modbus_gateway, cmd_topic, open, timeout_sec
        ),
        "charge": lambda x, y, yaw: charge(gateway, x, y, yaw),
        "get_robot_state": lambda: get_robot_state(get_state_fn),
        "set_battery_level": lambda level: set_battery_level(gateway, level),
        # ROS CLI skills
        "ros2_topic_list": lambda: ros_cli.ros2_topic_list(),
        "ros2_topic_echo": lambda topic: ros_cli.ros2_topic_echo(topic),
        "ros2_topic_pub": lambda topic, msg_type, data: ros_cli.ros2_topic_pub(topic, msg_type, data),
        "ros2_service_list": lambda: ros_cli.ros2_service_list(),
        "ros2_service_call": lambda service_name, service_type, data: ros_cli.ros2_service_call(
            service_name, service_type, data
        ),
        "ros2_node_list": lambda: ros_cli.ros2_node_list(),
        "ros2_param_get": lambda node_name, param_name: ros_cli.ros2_param_get(node_name, param_name),
        "ros2_param_set": lambda node_name, param_name, value: ros_cli.ros2_param_set(
            node_name, param_name, value
        ),
    }