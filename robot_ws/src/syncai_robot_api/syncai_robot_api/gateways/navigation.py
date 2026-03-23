import math
import time
import structlog

from typing import Optional, Tuple

from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus


class NavigationGateway:

    def __init__(self, logger: structlog.stdlib.BoundLogger, node: Node, robot_id: str):
        self._logger = logger
        self._node = node
        self._robot_id = robot_id

        action_name = f'/{robot_id}/navigate_to_pose'
        self._nav_client = ActionClient(node, NavigateToPose, action_name)
        self._current_goal_handle: Optional[ClientGoalHandle] = None

        self._logger.info(
            "[NavigationGateway] Action client created",
            action_name=action_name
        )

    def navigate_to_pose(self, x: float, y: float, yaw: float) -> Tuple[bool, str]:
        if not self._nav_client.wait_for_server(timeout_sec=10.0):
            return False, "Navigation action server not available"

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self._node.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.x = 0.0
        goal_msg.pose.pose.orientation.y = 0.0
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self._logger.info(
            "[NavigationGateway] Sending goal",
            x=x, y=y, yaw=yaw
        )

        send_goal_future = self._nav_client.send_goal_async(goal_msg)

        while not send_goal_future.done():
            time.sleep(0.1)

        self._current_goal_handle = send_goal_future.result()

        if not self._current_goal_handle.accepted:
            self._current_goal_handle = None
            return False, "Goal rejected by navigation server"

        self._logger.info("[NavigationGateway] Goal accepted")

        result_future = self._current_goal_handle.get_result_async()
        while not result_future.done():
            time.sleep(0.1)

        result = result_future.result()
        self._current_goal_handle = None

        if result.status == GoalStatus.STATUS_SUCCEEDED:
            return True, "Navigation succeeded"
        elif result.status == GoalStatus.STATUS_CANCELED:
            return False, "Navigation was cancelled"
        else:
            error_msg = getattr(result.result, 'error_msg', 'Unknown error')
            return False, f"Navigation failed: {error_msg}"

    def cancel_current_goal(self) -> bool:
        if self._current_goal_handle is None:
            return False

        self._logger.info("[NavigationGateway] Cancelling current goal")
        cancel_future = self._current_goal_handle.cancel_goal_async()
        while not cancel_future.done():
            time.sleep(0.1)

        return True


def init_navigation_gateway(
    logger: structlog.stdlib.BoundLogger,
    node: Node,
    robot_id: str
) -> NavigationGateway:
    return NavigationGateway(logger=logger, node=node, robot_id=robot_id)
