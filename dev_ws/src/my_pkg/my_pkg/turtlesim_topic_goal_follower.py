import math
import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist, Point


def wrap_to_pi(a: float) -> float:
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


class TopicGoalFollower(Node):
    def __init__(self):
        super().__init__("topic_goal_follower")

        # 2개 구독: pose(센서), goal(외부 입력)
        self.sub_pose = self.create_subscription(Pose, "/turtle1/pose", self.cb_pose, 10)
        self.sub_goal = self.create_subscription(Point, "/goal", self.cb_goal, 10)

        # 1개 발행: cmd_vel
        self.pub_cmd = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)

        self.pose = None
        self.goal = None

        # 제어 변수: 엄청나게 정교하진 않고 각도오차/거리만 반영
        self.k_lin = 1.0
        self.k_ang = 3.0
        self.max_lin = 2.0
        self.max_ang = 4.0
        self.stop_dist = 0.2

        # 콜백은 저장만, 실제 계산은 timer에서
        self.create_timer(0.05, self.tick)  # 20Hz
        self.get_logger().info("Waiting for /goal (geometry_msgs/Point)...")

    def cb_pose(self, msg: Pose):
        self.pose = msg

    def cb_goal(self, msg: Point):
        self.goal = msg
        self.get_logger().info(f"New goal: x={msg.x:.2f}, y={msg.y:.2f}")

    def clamp(self, x, lo, hi):
        return max(lo, min(hi, x))

    def tick(self):
        if self.pose is None or self.goal is None:
            return

        dx = self.goal.x - self.pose.x
        dy = self.goal.y - self.pose.y
        dist = math.hypot(dx, dy)

        cmd = Twist()

        # 목표 근처면 정지
        if dist < self.stop_dist:
            self.pub_cmd.publish(cmd)
            return

        target = math.atan2(dy, dx)
        err = wrap_to_pi(target - self.pose.theta)

        # 각도 오차가 크면 회전 위주
        if abs(err) > 0.7:
            cmd.linear.x = 0.0
            cmd.angular.z = self.clamp(self.k_ang * err, -self.max_ang, self.max_ang)
        else:
            cmd.linear.x = self.clamp(self.k_lin * dist, 0.0, self.max_lin)
            cmd.angular.z = self.clamp(self.k_ang * err, -self.max_ang, self.max_ang)

        self.pub_cmd.publish(cmd)


def main():
    rclpy.init()
    node = TopicGoalFollower()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()