import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint  # ① 메시지 타입
from builtin_interfaces.msg import Duration

class TrajectoryPublisher(Node):
    def __init__(self):
        super().__init__('trajectory_publisher')
        self.pub = self.create_publisher(
            JointTrajectory,                          # ② 메시지 타입
            '/joint_trajectory_controller/joint_trajectory',        # ③ 토픽 이름
            10
        )
        # 1초 후 한 번만 실행되는 타이머 생성
        self.timer = self.create_timer(1.0, self.publish_once)  # ④ 대기 시간(초)

    def publish_once(self):
        self.timer.cancel()  # 타이머 중지 (한 번만 실행)

        msg = JointTrajectory()           # ⑤ 메시지 객체 생성
        msg.joint_names = ['joint1_z', 'joint1_y', 'joint2', 'joint3']

        pt = JointTrajectoryPoint()
        pt.positions = [0.5, 0.3, -0.5, 0.2]    # ⑥ 목표 위치 리스트 입력
        pt.time_from_start = Duration(sec=2, nanosec=0)  # ⑦ 도달 시간

        msg.points = [pt]
        self.pub.publish(msg)                   # ⑧ 퍼블리시

        self.get_logger().info('[trajectory_publisher] 목표 자세 발행 완료!')
        raise SystemExit

def main():
    rclpy.init()
    node = TrajectoryPublisher()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()