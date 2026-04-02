"""
Test node for bridge command service.
Subscribes to bridge_cmd, echoes back a success response on bridge_cmd_resp.

Usage:
    ros2 run syncai_robot_api test_bridge_cmd --ros-args -r __ns:=/robot01
"""
import rclpy
from rclpy.node import Node

from syncai_common.msg import BridgeCommand, BridgeCommandResponse


class BridgeCmdTestNode(Node):

    def __init__(self):
        super().__init__('bridge_cmd_test')

        self.sub = self.create_subscription(
            BridgeCommand, 'bridge_cmd', self.on_cmd, 10
        )
        self.pub = self.create_publisher(
            BridgeCommandResponse, 'bridge_cmd_resp', 10
        )
        self.get_logger().info('Bridge command test node started — waiting for commands...')

    def on_cmd(self, msg: BridgeCommand):
        self.get_logger().info(
            f'Received command: request_id={msg.request_id} '
            f'action={msg.action} payload={msg.payload_json}'
        )

        resp = BridgeCommandResponse()
        resp.request_id = msg.request_id
        resp.success = True
        resp.message = f'echo: {msg.action} done'
        resp.data_json = '{}'
        self.pub.publish(resp)

        self.get_logger().info(f'Sent response: request_id={msg.request_id} success=True')


def main(args=None):
    rclpy.init(args=args)
    node = BridgeCmdTestNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
