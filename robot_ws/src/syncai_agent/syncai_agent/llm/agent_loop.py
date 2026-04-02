import json
import structlog

from syncai_agent.llm.client import LLMClient
from syncai_agent.llm.tools import TOOLS


SYSTEM_PROMPT = """You are an AI agent controlling a ROS 2 mobile robot (AMR). You can navigate, open/close doors, charge, and inspect the ROS system.

## Available Skills

### High-level robot actions (preferred when applicable):
- **navigate_to_pose**: Move the robot to a map coordinate (x, y in meters, yaw in degrees)
- **navigate_with_alert**: Navigate with safety alerts (for cautious movement)
- **control_door**: Open or close a door via its command/state topics
- **charge**: Navigate to a charging station and dock to recharge
- **get_robot_state**: Get current position, velocity, and battery level
- **set_battery_level**: Set simulated battery level (testing only)

### ROS CLI tools (for introspection and low-level operations):
- **ros2_topic_list**: List all ROS topics
- **ros2_topic_echo**: Read one message from a topic
- **ros2_topic_pub**: Publish a message to a topic
- **ros2_service_list**: List all ROS services
- **ros2_service_call**: Call any ROS service
- **ros2_node_list**: List active ROS nodes
- **ros2_param_get / ros2_param_set**: Read or write node parameters

## Guidelines
- Use high-level skills (navigate_to_pose, charge, etc.) when they match the task.
- Use ROS CLI tools for introspection (listing topics, reading sensor data) or for operations not covered by the high-level skills.
- Always check robot state before navigation if the user hasn't provided coordinates.
- Report results clearly: success/failure, current position after navigation, etc.
- Coordinates are in the map frame (meters). Yaw is in degrees (0 = facing +X axis).
"""


class AgentLoop:

    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger,
        llm_client: LLMClient,
        skills: dict,
        robot_id: str,
    ):
        self._log = logger
        self._llm = llm_client
        self._skills = skills
        self._messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT + f"\nYou are controlling robot: {robot_id}",
            }
        ]

    def process_user_input(self, user_message: str) -> str:
        self._messages.append({"role": "user", "content": user_message})

        max_iterations = 10
        for _ in range(max_iterations):
            response = self._llm.chat(self._messages, TOOLS)
            choice = response.choices[0]

            if choice.finish_reason == "stop":
                self._messages.append(choice.message.model_dump())
                return choice.message.content or ""

            if choice.finish_reason == "tool_calls":
                self._messages.append(choice.message.model_dump())

                for tool_call in choice.message.tool_calls:
                    fn_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    self._log.info("[AgentLoop] Executing tool", tool=fn_name, args=args)

                    if fn_name in self._skills:
                        try:
                            result = self._skills[fn_name](**args)
                        except Exception as e:
                            result = {"success": False, "error": str(e)}
                    else:
                        result = {"success": False, "error": f"Unknown tool: {fn_name}"}

                    self._messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    })
                continue

            # Unexpected finish reason
            self._log.warning("[AgentLoop] Unexpected finish reason", reason=choice.finish_reason)
            return choice.message.content or "(No response)"

        return "(Agent reached maximum iterations)"

    def reset_conversation(self):
        system_msg = self._messages[0]
        self._messages = [system_msg]
