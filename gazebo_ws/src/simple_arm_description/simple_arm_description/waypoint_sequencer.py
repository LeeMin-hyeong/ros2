import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

JOINT_NAMES = ['joint1_z', 'joint1_y', 'joint2', 'joint3']

# (목표 위치 리스트, 다음 WP까지 대기 틱 수)
WAYPOINTS = [
    ([0.0,  0.0,  0.0, 0.0], 3),   # WP 0: Home
    ([0.5,  0.0,  0.0, 0.0], 3),   # WP 1: joint1_z
    ([0.5,  0.3,  0.0, 0.0], 3),   # WP 2: joint1_y
    ([0.5,  0.3, -0.5, 0.2], 2),   # WP 3: 최종 (2틱 후 종료)
]

class WaypointSequencer(Node):
    def __init__(self):
        super().__init__('waypoint_sequencer')
        self.pub = self.create_publisher(
            JointTrajectory,                          # ① 메시지 타입
            '/joint_trajectory_controller/joint_trajectory',        # ② 토픽 이름
            10
        )
        self.timer  = self.create_timer(1.0, self.tick) # ③ 타이머 주기(초)
        self.wp_idx = 0       # 현재 waypoint 인덱스
        self.ticks  = 0       # 현재 WP 발행 후 경과 틱 수
        self.done   = False   # 시퀀스 완료 여부

    def publish_wp(self, idx):
        positions, _ = WAYPOINTS[idx]
        msg = JointTrajectory()
        msg.joint_names = JOINT_NAMES
        pt = JointTrajectoryPoint()
        pt.positions = positions              # ④ 목표 위치 할당
        pt.time_from_start = Duration(sec=2, nanosec=0)  # ⑤ 도달 시간
        msg.points = [pt]
        self.pub.publish(msg)                 # ⑥ 퍼블리시
        names = dict(zip(JOINT_NAMES, positions))
        self.get_logger().info(
            f'[WP {idx}/{len(WAYPOINTS)-1}]'
            f' joint1_z={names["joint1_z"]}, joint1_y={names["joint1_y"]},'
            f' joint2={names["joint2"]}, joint3={names["joint3"]}'
        )

    def tick(self):
        if self.done:
            return

        # 첫 tick: WP 0 즉시 발행
        if self.wp_idx == 0 and self.ticks == 0:
            self.publish_wp(0)
            self.ticks += 1
            return

        _, wait = WAYPOINTS[self.wp_idx]
        self.ticks += 1

        # ⑦ 대기 틱이 됐을 때 다음 WP 발행 또는 종료 처리
        if self.ticks > wait:
            self.wp_idx += 1
            self.ticks  = 0
            if self.wp_idx >= len(WAYPOINTS):             # ⑧ 전체 WP 수
                self.get_logger().info('모든 waypoint 완료. 노드 종료.')
                self.done = True
                raise SystemExit
            self.publish_wp(self.wp_idx)       # ⑨ 다음 WP 발행

def main():
    rclpy.init()
    node = WaypointSequencer()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()
