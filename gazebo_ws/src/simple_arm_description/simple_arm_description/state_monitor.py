import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState  # ① 어떤 패키지의 메시지인가?

TARGETS = ['joint1_z', 'joint1_y', 'joint2', 'joint3']
PRINT_HZ = 2.0  # 출력 주기 (Hz)

class StateMonitor(Node):
    def __init__(self):
        super().__init__('state_monitor')
        self.data = {}  # 최신 joint 상태 저장용

        self.create_subscription(
            JointState,              # ② 메시지 타입
            'joint_states',            # ③ 구독할 토픽 이름
            self.callback,
            10
        )
        self.create_timer(1.0 / PRINT_HZ, self.print_state)  # ④ 출력 주기(초) 계산

    def callback(self, msg):
        # 아래 딕셔너리 생성 코드는 완성된 상태입니다
        self.data = {n: (p, v) for n, p, v in
                     zip(msg.name, msg.position, msg.velocity)}

    def print_state(self):
        if not self.data:              # ⑤ 아직 데이터가 없으면 건너뜀
            return
        for name in TARGETS:
            if name not in self.data:
                continue
            pos, vel = self.data[name]   # ⑥ self.data 에서 값 꺼내기
            self.get_logger().info(
                f'[state_monitor] {name:<10} pos: {pos:.3f}  vel: {vel:.3f}'
            )

def main():
    rclpy.init()
    node = StateMonitor()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()