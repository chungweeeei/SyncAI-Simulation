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
from syncai_bt_plugins.action import DoorControl, Charging, NavigateWithAlert


def _wait_for_future(future, timeout: Optional[float] = None) -> bool:
    event = threading.Event()
    future.add_done_callback(lambda _: event.set())
    return event.wait(timeout=timeout)


class RobotGateway:

    def __init__(self, logger: structlog.stdlib.BoundLogger, node: Node, robot_id: str):
        self._logger = logger
        self._node = node
        self._robot_id = robot_id

        # Navigation action client
        nav_action_name = f'/{robot_id}/navigate_to_pose'
        self._nav_client = ActionClient(node, NavigateToPose, nav_action_name)
        self._current_goal_handle: Optional[ClientGoalHandle] = None

        # Door control action client
        door_action_name = f'/{robot_id}/door_control'
        self._door_client = ActionClient(node, DoorControl, door_action_name)

        # Charging action client
        charging_action_name = f'/{robot_id}/charging'
        self._charging_client = ActionClient(node, Charging, charging_action_name)

        # Navigate with alert action client
        navigate_with_alert_action_name = f'/{robot_id}/navigate_with_alert'
        self._navigate_with_alert_client = ActionClient(node, NavigateWithAlert, navigate_with_alert_action_name)

        self._logger.info(
            "[RobotGateway] Action clients created",
            nav_action=nav_action_name,
            door_action=door_action_name,
            charging_action=charging_action_name,
            navigate_with_alert_action=navigate_with_alert_action_name,
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

        self._logger.info("[RobotGateway] Sending navigate goal", x=x, y=y, yaw=yaw)

        send_goal_future = self._nav_client.send_goal_async(goal_msg)
        if not _wait_for_future(send_goal_future, timeout=15.0):
            return False, "Timeout waiting for goal acceptance"

        self._current_goal_handle = send_goal_future.result()

        if not self._current_goal_handle.accepted:
            self._current_goal_handle = None
            return False, "Goal rejected by navigation server"

        self._logger.info("[RobotGateway] Navigate goal accepted")

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

    def control_door(
        self,
        cmd_topic: str,
        state_topic: str,
        open: bool = True,
        timeout_sec: float = 10.0,
    ) -> Tuple[bool, str]:
        if not self._door_client.wait_for_server(timeout_sec=10.0):
            return False, "Door control action server not available"

        goal_msg = DoorControl.Goal()
        goal_msg.cmd_topic = cmd_topic
        goal_msg.state_topic = state_topic
        goal_msg.open = open
        goal_msg.timeout_sec = timeout_sec

        action_str = "open" if open else "close"
        self._logger.info(
            f"[RobotGateway] Sending door {action_str} goal",
            cmd_topic=cmd_topic,
            state_topic=state_topic,
        )

        send_goal_future = self._door_client.send_goal_async(goal_msg)
        if not _wait_for_future(send_goal_future, timeout=15.0):
            return False, "Timeout waiting for door control goal acceptance"

        self._current_goal_handle = send_goal_future.result()

        if not self._current_goal_handle.accepted:
            self._current_goal_handle = None
            return False, "Door control goal rejected"

        self._logger.info(f"[RobotGateway] Door {action_str} goal accepted")

        result_future = self._current_goal_handle.get_result_async()
        _wait_for_future(result_future, timeout=timeout_sec + 5.0)

        result = result_future.result()
        self._current_goal_handle = None

        if result.status == GoalStatus.STATUS_SUCCEEDED:
            return True, result.result.message
        elif result.status == GoalStatus.STATUS_CANCELED:
            return False, "Door control was cancelled"
        else:
            return False, result.result.message

    def charge(
        self,
        x: float,
        y: float,
        yaw: float,
        recharge_service: str = "recharge",
    ) -> Tuple[bool, str]:
        if not self._charging_client.wait_for_server(timeout_sec=10.0):
            return False, "Charging action server not available"

        goal_msg = Charging.Goal()
        goal_msg.target_x = x
        goal_msg.target_y = y
        goal_msg.target_yaw = yaw
        goal_msg.recharge_service = recharge_service

        self._logger.info(
            "[RobotGateway] Sending charging goal",
            x=x, y=y, yaw=yaw,
        )

        send_goal_future = self._charging_client.send_goal_async(goal_msg)
        if not _wait_for_future(send_goal_future, timeout=15.0):
            return False, "Timeout waiting for charging goal acceptance"

        self._current_goal_handle = send_goal_future.result()

        if not self._current_goal_handle.accepted:
            self._current_goal_handle = None
            return False, "Charging goal rejected"

        self._logger.info("[RobotGateway] Charging goal accepted")

        result_future = self._current_goal_handle.get_result_async()
        _wait_for_future(result_future)

        result = result_future.result()
        self._current_goal_handle = None

        if result.status == GoalStatus.STATUS_SUCCEEDED:
            return True, result.result.message
        elif result.status == GoalStatus.STATUS_CANCELED:
            return False, "Charging was cancelled"
        else:
            return False, result.result.message

    def navigate_with_alert(
        self,
        x: float,
        y: float,
        yaw: float,
    ) -> Tuple[bool, str]:
        if not self._navigate_with_alert_client.wait_for_server(timeout_sec=10.0):
            return False, "Navigate with alert action server not available"

        goal_msg = NavigateWithAlert.Goal()
        goal_msg.target_x = x
        goal_msg.target_y = y
        goal_msg.target_yaw = yaw

        self._logger.info(
            "[RobotGateway] Sending navigate with alert goal",
            x=x, y=y, yaw=yaw,
        )

        send_goal_future = self._navigate_with_alert_client.send_goal_async(goal_msg)
        if not _wait_for_future(send_goal_future, timeout=15.0):
            return False, "Timeout waiting for navigate with alert goal acceptance"

        self._current_goal_handle = send_goal_future.result()

        if not self._current_goal_handle.accepted:
            self._current_goal_handle = None
            return False, "Navigate with alert goal rejected"

        self._logger.info("[RobotGateway] Navigate with alert goal accepted")

        result_future = self._current_goal_handle.get_result_async()
        _wait_for_future(result_future)

        result = result_future.result()
        self._current_goal_handle = None

        if result.status == GoalStatus.STATUS_SUCCEEDED:
            return True, result.result.message
        elif result.status == GoalStatus.STATUS_CANCELED:
            return False, "Navigate with alert was cancelled"
        else:
            return False, result.result.message

    def cancel_current_goal(self) -> bool:
        if self._current_goal_handle is None:
            return False

        self._logger.info("[RobotGateway] Cancelling current goal")
        cancel_future = self._current_goal_handle.cancel_goal_async()
        _wait_for_future(cancel_future, timeout=10.0)

        return True


def init_robot_gateway(
    logger: structlog.stdlib.BoundLogger,
    node: Node,
    robot_id: str
) -> RobotGateway:
    return RobotGateway(logger=logger, node=node, robot_id=robot_id)
