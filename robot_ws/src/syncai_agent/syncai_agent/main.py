import os
import configparser

import structlog
import rclpy

from syncai_agent.agent_node import SyncAIAgentNode


def _read_robot_id() -> str:
    data_dir = os.path.expanduser("~/data")
    config = configparser.ConfigParser()
    config.read(os.path.join(data_dir, "system.ini"))
    return config.get("identity", "robot_id", fallback="robot01")


def main():
    rclpy.init()

    logger = structlog.get_logger()

    # Read config
    robot_id = _read_robot_id()
    llm_api_key = os.environ.get("SYNCAI_LLM_API_KEY", "")
    llm_model = os.environ.get("SYNCAI_LLM_MODEL", "gpt-4o")

    if not llm_api_key:
        logger.error("[SyncAIAgent] SYNCAI_LLM_API_KEY environment variable is not set")
        rclpy.shutdown()
        return

    node = SyncAIAgentNode(
        logger=logger,
        robot_id=robot_id,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
    )

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
