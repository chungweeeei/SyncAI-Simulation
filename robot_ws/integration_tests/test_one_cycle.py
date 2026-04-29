"""Spawn the next box (box04) then run a single pickup + drop cycle."""
import math
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry


PICKUP_MAP  = (-3.45, 4.34)
PICKUP_USD  = (-2.0,  7.05)
STAGING_MAP = ( 4.50, -1.35)
STAGING_USD = ( 5.95,  1.36)


class N(Node):
    def __init__(self):
        super().__init__("one_cycle")
        self.belt = self.create_publisher(Float32, "/conveyor/conveyor_01/speed_cmd", 10)
        self.goal = self.create_publisher(PoseStamped, "/robot01/goal_pose", 10)
        self.drop = self.create_publisher(String, "/cargo/drop_cmd", 10)
        self.spawn = self.create_publisher(String, "/cargo/conveyor_01/spawn_cmd", 10)
        self.status = ""; self.pos = (0.0, 0.0)
        self.create_subscription(String, "/conveyor/conveyor_01/status",
                                  lambda m: setattr(self, "status", m.data), 10)
        self.create_subscription(Odometry, "/robot01/odom",
                                  lambda m: setattr(self, "pos",
                                                     (m.pose.pose.position.x, m.pose.pose.position.y)), 10)

    def spin(self, dt):
        end = time.time() + dt
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.05)

    def go(self, mx, my, yaw):
        ps = PoseStamped()
        ps.header.frame_id = "map"
        ps.header.stamp = self.get_clock().now().to_msg()
        ps.pose.position.x = mx; ps.pose.position.y = my
        cz, sz = math.cos(yaw/2), math.sin(yaw/2)
        ps.pose.orientation.w = cz; ps.pose.orientation.z = sz
        for _ in range(5):
            self.goal.publish(ps); self.spin(0.1)

    def wait_at(self, ux, uy, tol, timeout):
        end = time.time() + timeout
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.2)
            if math.hypot(self.pos[0]-ux, self.pos[1]-uy) < tol:
                return True
        return False

    def wait_status(self, prefix, timeout):
        end = time.time() + timeout
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.status.startswith(prefix): return True
        return False


def main():
    rclpy.init(); n = N(); n.spin(2.0)
    print(f"[t] start status={n.status!r} pos=({n.pos[0]:.2f},{n.pos[1]:.2f})")

    # Step 1: spawn next box (auto-increment, expect box04)
    print("[t] sending spawn_cmd")
    for i in range(3):
        rst = String(); rst.data = f"_reset_s_{i}_{int(time.time()*1000)%10000}"
        n.spawn.publish(rst); n.spin(0.4)
        msg = String(); msg.data = ""
        n.spawn.publish(msg); n.spin(0.6)
        rclpy.spin_once(n, timeout_sec=0.3)
        if n.status in ("stopped", "running"):
            print(f"[t] spawn ok status={n.status!r}")
            break
    n.spin(2.0)

    # Step 2: belt + drive to pickup
    m = Float32(); m.data = 0.3; n.belt.publish(m)
    print("[t] belt 0.3")
    n.go(PICKUP_MAP[0], PICKUP_MAP[1], math.pi/2)
    print(f"[t] driving to pickup ({PICKUP_USD})")
    n.wait_at(PICKUP_USD[0], PICKUP_USD[1], tol=0.6, timeout=120)
    print(f"[t] arrived pos=({n.pos[0]:.2f},{n.pos[1]:.2f})")

    if not n.wait_status("carried:", timeout=30):
        print(f"[t] FAIL never carried, status={n.status!r}"); return
    print(f"[t] {n.status}")
    carried_box = n.status.split(":",1)[1].split("@",1)[0]  # carried:box04@SyncRobot01 -> box04

    # Step 3: drive to staging
    n.go(STAGING_MAP[0], STAGING_MAP[1], -math.pi/2)
    print(f"[t] driving to staging ({STAGING_USD})")
    n.wait_at(STAGING_USD[0], STAGING_USD[1], tol=0.45, timeout=180)
    print(f"[t] arrived pos=({n.pos[0]:.2f},{n.pos[1]:.2f})")
    n.spin(2.0)

    # Step 4: drop
    payload = f"{carried_box}:dropoff_a"
    print(f"[t] sending drop_cmd payload={payload!r}")
    for i in range(8):
        rst = String(); rst.data = f"_reset_d_{i}"
        n.drop.publish(rst); n.spin(0.4)
        msg = String(); msg.data = payload
        n.drop.publish(msg); n.spin(0.6)
        rclpy.spin_once(n, timeout_sec=0.5)
        print(f"[t] drop attempt {i} status={n.status!r}")
        if n.status.startswith("dropped:"):
            break
        n.spin(1.0)

    print(f"\n[t] DONE final status={n.status!r}")
    n.destroy_node(); rclpy.shutdown()


if __name__ == "__main__":
    main()
