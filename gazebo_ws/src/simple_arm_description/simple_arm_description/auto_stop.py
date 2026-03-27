import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray


STOP_THRESHOLD = 0.8


class AutoStop(Node):
    def __init__(self):
        super().__init__("auto_stop")
        self.subscriber = self.create_subscription(JointState, "/joint_states", self.joint_cb, 10)
        self.publisher = self.create_publisher(Float64MultiArray, "/effort_controller/commands", 10)
        self.timer = self.create_timer(0.5, self.log_cb)
        self.joint3_pos = 0.0
        self.stopped = False

    def joint_cb(self, msg: JointState):
        # msg.name 과 msg.position 을 이용해 joint3 의 position 을 찾는다
        # ④ joint3 position 추출 (name 리스트에서 인덱스를 찾아 position에 적용)
        # 직접 작성 ↓
        if self.stopped or "joint3" not in msg.name:
            return

        joint3_index = msg.name.index("joint3")
        if joint3_index >= len(msg.position):
            return

        joint3_position = msg.position[joint3_index]
        self.joint3_pos = joint3_position

        if not self.stopped and abs(self.joint3_pos) > STOP_THRESHOLD:
            self.stopped = True
            stop_msg = Float64MultiArray()
            stop_msg.data = [0.0, 0.0, 0.0, 0.0]
            self.publisher.publish(stop_msg)

            self.get_logger().info(
                f"[AUTO STOP]  joint3 = {joint3_position:.3f} rad 도달 -> 전체 토크 해제"
            )
            self.destroy_node()
            rclpy.shutdown()

    def log_cb(self):
        if not self.stopped:
            self.get_logger().info(f'joint3 현재 위치: {self.joint3_pos:.3f} rad')

def main():
    rclpy.init()
    node = AutoStop()
    rclpy.spin(node)
    rclpy.shutdown()
