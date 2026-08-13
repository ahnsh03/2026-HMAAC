import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, Float32

from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSReliabilityPolicy

from .lib import lidar_perception_func_lib as LPFL
from .node_shutdown import install_shutdown

#---------------Variable Setting---------------
SUB_TOPIC_NAME = 'lidar_processed'
PUB_TOPIC_NAME = 'lidar_obstacle_info'
PUB_LANE1_MIN_TOPIC_NAME = 'lidar_lane1_min'
#----------------------------------------------

VALID_RMIN = 0.12
VALID_RMAX = 8.0


def sector_min(ranges, start_angle, end_angle, range_min=VALID_RMIN, range_max=VALID_RMAX):
    """섹터 안 유효 거리의 최소값. 없으면 inf. ANY-in-range가 아님."""
    n = len(ranges)
    if n == 0:
        return float('inf')
    start_angle = int(start_angle) % n
    end_angle = int(end_angle) % n
    if start_angle <= end_angle:
        indices = range(start_angle, end_angle + 1)
    else:
        indices = list(range(start_angle, n)) + list(range(0, end_angle + 1))
    found = float('inf')
    for i in indices:
        r = ranges[i]
        if math.isfinite(r) and range_min <= r <= range_max:
            if r < found:
                found = r
    return found


class ObjectDetection(Node):
    def __init__(self):
        super().__init__('lidar_obstacle_detector_node')

        self.qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1
        )

        # 전방 0–90°, 110 cm 이내 물체
        self.declare_parameter('lane1_start_angle', 0)
        self.declare_parameter('lane1_end_angle', 90)
        self.declare_parameter('stop_range_max', 1.10)

        self.subscriber = self.create_subscription(LaserScan, SUB_TOPIC_NAME, self.lidar_callback, self.qos_profile)
        self.publisher = self.create_publisher(Bool, PUB_TOPIC_NAME, self.qos_profile)
        self.lane1_pub = self.create_publisher(Float32, PUB_LANE1_MIN_TOPIC_NAME, self.qos_profile)

        self.detection_checker = LPFL.StabilityDetector(consec_count=3)

    def lidar_callback(self, msg):
        ranges = msg.ranges
        start_angle = int(self.get_parameter('lane1_start_angle').value)
        end_angle = int(self.get_parameter('lane1_end_angle').value)
        stop_range_max = float(self.get_parameter('stop_range_max').value)

        front_min = sector_min(ranges, start_angle, end_angle)
        detected = math.isfinite(front_min) and front_min <= stop_range_max
        detection_result = self.detection_checker.check_consecutive_detections(detected)

        detection_msg = Bool()
        detection_msg.data = detection_result
        self.publisher.publish(detection_msg)

        min_msg = Float32()
        min_msg.data = float(front_min)
        self.lane1_pub.publish(min_msg)

        self.get_logger().info(
            f'Lidar Obstacle detected: {detection_result} '
            f'front_min={front_min:.3f}'
        )


def main(args=None):
    install_shutdown()
    rclpy.init(args=args)
    object_detection_node = ObjectDetection()
    try:
        rclpy.spin(object_detection_node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        object_detection_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
