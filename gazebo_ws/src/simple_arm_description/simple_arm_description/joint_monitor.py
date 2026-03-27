import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


WARN_THRESHOLD = 1.0
TARGET_JOINTS = ["joint1_z", "joint1_y", "joint2", "joint3"]


class JointMonitor(Node):
    def __init__(self):
        super().__init__("joint_monitor")
        self.create_subscription(
            JointState,
            "/joint_states",
            self.callback,
            10
        )

    def callback(self, msg: JointState):
        pairs = dict(zip(msg.name, msg.position))
        
        line = "[joint_monitor]"
        for name, pos in pairs.items():
            line += f'  {name}: {pos:.3f}'
        self.get_logger().info(line)

        for name, pos in pairs.items():
            if pos >= WARN_THRESHOLD:
                self.get_logger().warn(
                    f'[WARNING]  {name} 이(가) {WARN_THRESHOLD} rad 를 초과! (현재: {pos:.3f})'
                )


def main(args=None):
    rclpy.init(args=args)
    node = JointMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
