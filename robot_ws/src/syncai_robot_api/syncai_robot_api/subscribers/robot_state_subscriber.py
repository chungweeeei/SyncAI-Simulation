import structlog

from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    QoSDurabilityPolicy,
    QoSReliabilityPolicy,
    QoSHistoryPolicy
)

from syncai_common.msg import RobotState as RobotStateMsg

from syncai_robot_api.repositories.robot.robot import RobotRepo
from syncai_robot_api.repositories.robot.schema import (
    RobotPose,
    RobotVelocity,
    RobotBattery,
    RobotState
)

from syncai_robot_api.helpers.math_helper import convert_quaternion_to_yaw

class RobotStateSubscriber:

    def __init__(self, logger: structlog.stdlib.BoundLogger, robot_repo: RobotRepo):
        self._logger = logger
        self._robot_repo = robot_repo

    def register(self, node: Node):

        self._robot_state_sub = node.create_subscription(
            msg_type=RobotStateMsg,
            topic="robot_state",
            callback=self._robot_state_cb,
            qos_profile=QoSProfile(
                depth=5,
                reliability=QoSReliabilityPolicy.BEST_EFFORT,
                durability=QoSDurabilityPolicy.VOLATILE,
                history=QoSHistoryPolicy.KEEP_LAST
            )
        )
        
    def _robot_state_cb(self, msg: RobotStateMsg):

        timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        state = RobotState(
            timestamp=timestamp,
            robot_id=msg.robot_id,
            robot_name=msg.robot_name,
            model=msg.model,
            map=msg.map,
            pose=RobotPose(
                x = msg.pose.position.x,
                y = msg.pose.position.y,
                yaw = convert_quaternion_to_yaw(
                    x=msg.pose.orientation.x,
                    y=msg.pose.orientation.y,
                    z=msg.pose.orientation.z,
                    w=msg.pose.orientation.w
                )
            ),
            velocity=RobotVelocity(
                vx=msg.velocity.linear.x,
                vy=msg.velocity.linear.y,
                omega=msg.velocity.angular.z
            ),
            battery=RobotBattery(
                percentage=msg.battery_percentage,
                voltage=msg.battery_voltage
            )
        )

        self._robot_repo.update_robot_state(state=state)


def init_robot_state_subscriber(
    logger: structlog.stdlib.BoundLogger, 
    node: Node,
    robot_repo: RobotRepo
) -> None:
    robot_state_subscriber = RobotStateSubscriber(logger=logger, robot_repo=robot_repo)
    robot_state_subscriber.register(node=node)