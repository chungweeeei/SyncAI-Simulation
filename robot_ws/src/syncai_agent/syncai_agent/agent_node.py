import threading
import structlog

from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    QoSDurabilityPolicy,
    QoSReliabilityPolicy,
    QoSHistoryPolicy,
)

from syncai_common.msg import RobotState as RobotStateMsg

from syncai_agent.gateway.robot_gateway import RobotGateway
from syncai_robot_api.gateways.modbus import ModbusGateway
from syncai_agent.skills import build_skills
from syncai_agent.llm.client import LLMClient
from syncai_agent.llm.agent_loop import AgentLoop


class SyncAIAgentNode(Node):

    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger,
        robot_id: str,
        llm_api_key: str,
        llm_model: str,
    ):
        super().__init__('syncai_agent')
        self._log = logger

        # Robot state cache
        self._robot_state = None
        self._state_lock = threading.Lock()

        # Subscribe to robot state
        self._state_sub = self.create_subscription(
            msg_type=RobotStateMsg,
            topic='robot_state',
            callback=self._robot_state_cb,
            qos_profile=QoSProfile(
                depth=5,
                reliability=QoSReliabilityPolicy.BEST_EFFORT,
                durability=QoSDurabilityPolicy.VOLATILE,
                history=QoSHistoryPolicy.KEEP_LAST,
            ),
        )

        # Robot gateway (action clients + service clients)
        self._gateway = RobotGateway(logger=logger, node=self, robot_id=robot_id)

        # Modbus gateway (door control via Modbus TCP)
        self._modbus_gateway = ModbusGateway(logger=logger)

        # Build skills
        skills = build_skills(
            gateway=self._gateway,
            modbus_gateway=self._modbus_gateway,
            get_state_fn=self._get_robot_state,
        )

        # LLM client and agent loop
        llm_client = LLMClient(logger=logger, api_key=llm_api_key, model=llm_model)
        self._agent_loop = AgentLoop(
            logger=logger,
            llm_client=llm_client,
            skills=skills,
            robot_id=robot_id,
        )

        # Start CLI in daemon thread
        self._cli_thread = threading.Thread(target=self._run_cli, daemon=True)
        self._cli_thread.start()

        self._log.info("[SyncAIAgent] Agent node started", robot_id=robot_id, model=llm_model)

    def _robot_state_cb(self, msg: RobotStateMsg):
        with self._state_lock:
            self._robot_state = {
                "robot_id": msg.robot_id,
                "pose": {
                    "x": msg.pose.position.x,
                    "y": msg.pose.position.y,
                    "yaw": self._quaternion_to_yaw(msg.pose.orientation),
                },
                "velocity": {
                    "vx": msg.velocity.linear.x,
                    "vy": msg.velocity.linear.y,
                    "omega": msg.velocity.angular.z,
                },
                "battery": {
                    "percentage": msg.battery_percentage,
                    "voltage": msg.battery_voltage,
                },
            }

    def _get_robot_state(self):
        with self._state_lock:
            return self._robot_state

    @staticmethod
    def _quaternion_to_yaw(orientation):
        import math
        siny_cosp = 2.0 * (orientation.w * orientation.z + orientation.x * orientation.y)
        cosy_cosp = 1.0 - 2.0 * (orientation.y * orientation.y + orientation.z * orientation.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def _run_cli(self):
        print("\n" + "=" * 60)
        print("  SyncAI Agent - Interactive CLI")
        print("  Type your command in natural language.")
        print("  Type 'reset' to clear conversation history.")
        print("  Type 'exit' or 'quit' to stop.")
        print("=" * 60 + "\n")

        while True:
            try:
                user_input = input("You > ").strip()
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Agent shutting down.")
                break
            if user_input.lower() == "reset":
                self._agent_loop.reset_conversation()
                print("Conversation history cleared.\n")
                continue

            print("Agent is thinking...")
            response = self._agent_loop.process_user_input(user_input)
            print(f"\nAgent > {response}\n")
