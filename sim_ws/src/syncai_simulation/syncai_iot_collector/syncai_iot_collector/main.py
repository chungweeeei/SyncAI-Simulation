import os
import yaml

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

from syncai_iot_collector.gateways.agent import init_agent_gateway
from syncai_iot_collector.subscribers.alarm_subscriber import init_alarm_subscriber
from syncai_iot_collector.subscribers.door_subscriber import init_door_subscriber

class IotCollectorNode(Node):

    def __init__(self) -> None:
        super().__init__('syncai_iot_collector')
        self._logger = self.get_logger()

        agent_gateway = init_agent_gateway(logger=self._logger)

        devices = self._load_iot_devices()
        for device in devices:
            device_id = device["id"]
            device_type = device["type"]

            if device_type == "alarm":
                init_alarm_subscriber(node=self, device_id=device_id,
                                      agent_gateway=agent_gateway)
            elif device_type == "door":
                init_door_subscriber(node=self, device_id=device_id,
                                     agent_gateway=agent_gateway)
            else:
                self._logger.warning(f"Unknown device type: {device_type}")

        self._logger.info(f"[IotCollector] Registered {len(devices)} IoT device subscribers")

    def _load_iot_devices(self) -> list:
        config_path = os.path.join(
            get_package_share_directory("syncai_iot_collector"), "config", "iot_devices.yaml"
        )
        try:
            with open(config_path, "r") as f:
                config = yaml.load(f, Loader=yaml.CLoader)
        except Exception as err:
            self._logger.warning(f"Failed to load IoT device config, error={err}")
            return []

        return config.get("devices", [])

def main(args=None) -> None:
    rclpy.init(args=args)
    node = IotCollectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
