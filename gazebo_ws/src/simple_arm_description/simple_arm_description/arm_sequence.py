import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray


PHASES = [
    (5.0, [0.0, 0.0, 0.0, 0.0]),
    (5.0, [8.0, 0.0, 0.0, 0.0]),
    (5.0, [0.0, 8.0, 0.0, 0.0]),
    (5.0, [0.0, 0.0, 8.0, 0.0]),
    (None, [0.0, 0.0, 0.0, 0.0]),
]


class ArmSequencer(Node):
    def __init__(self):
        super().__init__("arm_sequencer")
        self.publisher = self.create_publisher(
            Float64MultiArray,
            "/effort_controller/commands",
            10
        )
        self.timer = self.create_timer(1, self.callback)
        self.start_time = self.get_clock().now()
        self.current_phase = 0
        self.phase_start   = self.get_clock().now()

    def callback(self):
        duration, data = PHASES[self.current_phase]

        if duration is not None:
            elapsed = (self.get_clock().now() - self.phase_start).nanoseconds / 1e9
            if elapsed >= duration:
                self.current_phase += 1
                self.phase_start = self.get_clock().now()
                duration, data = PHASES[self.current_phase]

        msg = Float64MultiArray()
        msg.data = data
        self.publisher.publish(msg)
        self.get_logger().info(
            f'[Phase {self.current_phase}]  data={data}'
        )

def main():
    rclpy.init()
    node = ArmSequencer()
    rclpy.spin(node)
    rclpy.shutdown()
