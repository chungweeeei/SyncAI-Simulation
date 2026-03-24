import math
import threading
import structlog

from typing import Optional, Tuple

from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus


def _wait_for_future(future, timeout: Optional[float] = None) -> bool:
    event = threading.Event()
    future.add_done_callback(lambda _: event.set())
    return event.wait(timeout=timeout)


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

        # Send goal and wait for acceptance
        send_goal_future = self._nav_client.send_goal_async(goal_msg)
        if not _wait_for_future(send_goal_future, timeout=15.0):
            return False, "Timeout waiting for goal acceptance"

        self._current_goal_handle = send_goal_future.result()

        if not self._current_goal_handle.accepted:
            self._current_goal_handle = None
            return False, "Goal rejected by navigation server"

        self._logger.info("[NavigationGateway] Goal accepted")

        # Wait for navigation result (no timeout — nav can take a long time)
        result_future = self._current_goal_handle.get_result_async()
        _wait_for_future(result_future)

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
        _wait_for_future(cancel_future, timeout=10.0)

        return True


def init_navigation_gateway(
    logger: structlog.stdlib.BoundLogger,
    node: Node,
    robot_id: str
) -> NavigationGateway:
    return NavigationGateway(logger=logger, node=node, robot_id=robot_id)
