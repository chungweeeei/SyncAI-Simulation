TOOLS = [
    # --- High-level robot skills ---
    {
        "type": "function",
        "function": {
            "name": "navigate_to_pose",
            "description": "Navigate the robot to a specific position on the map. This is a blocking call that waits until the robot arrives or fails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "X coordinate in map frame (meters)"},
                    "y": {"type": "number", "description": "Y coordinate in map frame (meters)"},
                    "yaw": {"type": "number", "description": "Target orientation in degrees (0=facing +X, 90=facing +Y)"},
                },
                "required": ["x", "y", "yaw"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "navigate_with_alert",
            "description": "Navigate the robot to a position with safety alerts enabled. Use this when the robot needs to navigate through areas that require extra caution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "X coordinate in map frame (meters)"},
                    "y": {"type": "number", "description": "Y coordinate in map frame (meters)"},
                    "yaw": {"type": "number", "description": "Target orientation in degrees"},
                },
                "required": ["x", "y", "yaw"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_door",
            "description": "Open or close a door. Requires the door's command and state topics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd_topic": {"type": "string", "description": "ROS topic to send door commands (e.g. '/door/door_01/command')"},
                    "state_topic": {"type": "string", "description": "ROS topic to read door state (e.g. '/door/door_01/state')"},
                    "open": {"type": "boolean", "description": "True to open the door, False to close it", "default": True},
                    "timeout_sec": {"type": "number", "description": "Timeout in seconds", "default": 10.0},
                },
                "required": ["cmd_topic", "state_topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "charge",
            "description": "Navigate to a charging station and start charging. The robot will dock and recharge its battery.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "X coordinate near the charging station (meters)"},
                    "y": {"type": "number", "description": "Y coordinate near the charging station (meters)"},
                    "yaw": {"type": "number", "description": "Orientation facing the dock in degrees"},
                },
                "required": ["x", "y", "yaw"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_robot_state",
            "description": "Get the current robot state including position, velocity, and battery level.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_battery_level",
            "description": "Set the simulated battery level (for testing/simulation only).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "number", "description": "Battery level percentage (0.0 to 100.0)"},
                },
                "required": ["level"],
            },
        },
    },
    # --- ROS CLI tools ---
    {
        "type": "function",
        "function": {
            "name": "ros2_topic_list",
            "description": "List all available ROS 2 topics.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ros2_topic_echo",
            "description": "Read a single message from a ROS 2 topic. Returns one message then stops.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic name (e.g. '/robot01/scan')"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ros2_topic_pub",
            "description": "Publish a single message to a ROS 2 topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic name"},
                    "msg_type": {"type": "string", "description": "Message type (e.g. 'std_msgs/msg/String')"},
                    "data": {"type": "string", "description": "YAML-formatted message data (e.g. '{data: hello}')"},
                },
                "required": ["topic", "msg_type", "data"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ros2_service_list",
            "description": "List all available ROS 2 services.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ros2_service_call",
            "description": "Call a ROS 2 service with the given type and data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Service name (e.g. '/robot01/set_battery_level')"},
                    "service_type": {"type": "string", "description": "Service type (e.g. 'syncai_common/srv/SetBatteryLevel')"},
                    "data": {"type": "string", "description": "YAML-formatted request data (e.g. '{level: 80.0}')"},
                },
                "required": ["service_name", "service_type", "data"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ros2_node_list",
            "description": "List all active ROS 2 nodes.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ros2_param_get",
            "description": "Get a parameter value from a ROS 2 node.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {"type": "string", "description": "Full node name (e.g. '/robot01/controller_server')"},
                    "param_name": {"type": "string", "description": "Parameter name (e.g. 'max_vel_x')"},
                },
                "required": ["node_name", "param_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ros2_param_set",
            "description": "Set a parameter value on a ROS 2 node.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {"type": "string", "description": "Full node name"},
                    "param_name": {"type": "string", "description": "Parameter name"},
                    "value": {"type": "string", "description": "New parameter value (as string)"},
                },
                "required": ["node_name", "param_name", "value"],
            },
        },
    },
]
