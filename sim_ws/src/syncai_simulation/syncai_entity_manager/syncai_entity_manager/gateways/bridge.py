import subprocess
from typing import Dict, List

from rclpy.impl.rcutils_logger import RcutilsLogger

BRIDGE_TOPIC_MAP: Dict[str, List[str]] = {
    'door': [
        '/{type}/{name}/cmd_topic@std_msgs/msg/Bool]gz.msgs.Boolean',
        '/{type}/{name}/state@std_msgs/msg/String[gz.msgs.StringMsg',
    ],
    'alarm': [
        '/{type}/{name}/cmd_topic@std_msgs/msg/Bool]gz.msgs.Boolean',
        '/{type}/{name}/state@std_msgs/msg/String[gz.msgs.StringMsg',
    ],
}


class BridgeGateway:

    def __init__(self, logger: RcutilsLogger):
        self._logger = logger
        self._bridges: Dict[str, subprocess.Popen] = {}

    def add_bridge(self, entity_name: str, model_type: str) -> None:
        templates = BRIDGE_TOPIC_MAP.get(model_type, [])
        if not templates:
            self._logger.info(f'[BridgeGateway] No bridge topics defined for {model_type}, skipping')
            return

        topics = [t.format(type=model_type, name=entity_name) for t in templates]

        cmd = ['ros2', 'run', 'ros_gz_bridge', 'parameter_bridge'] + topics
        self._logger.info(f'[BridgeGateway] Starting bridge for {entity_name}: {topics}')

        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self._bridges[entity_name] = proc

    def remove_bridge(self, entity_name: str) -> None:
        proc = self._bridges.pop(entity_name, None)
        if proc is None:
            return

        self._logger.info(f'[BridgeGateway] Terminating bridge for {entity_name}')
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._logger.warning(f'[BridgeGateway] Bridge did not terminate, killing: {entity_name}')
            proc.kill()
            proc.wait(timeout=2)

    def shutdown_all(self) -> None:
        for entity_name in list(self._bridges.keys()):
            self.remove_bridge(entity_name)
