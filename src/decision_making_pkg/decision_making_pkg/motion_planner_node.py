import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSReliabilityPolicy

from std_msgs.msg import String, Bool, Float32, Float32MultiArray
from interfaces_pkg.msg import PathPlanningResult, DetectionArray, MotionCommand
from .lib import decision_making_func_lib as DMFL
from .node_shutdown import install_shutdown

#---------------Variable Setting---------------
SUB_DETECTION_TOPIC_NAME = "detections"
SUB_PATH_TOPIC_NAME = "path_planning_result"
SUB_TRAFFIC_LIGHT_TOPIC_NAME = "yolov8_traffic_light_info"
SUB_LIDAR_OBSTACLE_TOPIC_NAME = "lidar_obstacle_info"
SUB_LIDAR_LANE1_MIN_TOPIC_NAME = "lidar_lane1_min"
SUB_LANE_CONTROL_TOPIC_NAME = "lane_control_info"
SUB_FORCE_START_TOPIC_NAME = "force_start"
PUB_TOPIC_NAME = "topic_control_signal"
PUB_FINISH_REASON_TOPIC_NAME = "finish_stop_reason"

#----------------------------------------------

TIMER = 0.1
NEED_GREEN_HITS = 3
NEED_FINISH_HITS = 3

# 라이다 단일: 0–90° 최소거리 ≤ 1.10 m. 카메라는 이 실험에서 쓰지 않음.
LIDAR_STOP_RMIN = 0.12
LIDAR_STOP_RMAX = 1.00

# 실차 P: 속도 250, k=0.028에서 점선을 밟지 않음. EMA/slew는 끈 상태가 기본.
DRIVE_SPEED = 250
STEER_MAX = 7
STEER_K = 0.028
STEER_ALPHA = 1.0
STEER_RATE = 7.0
VEHICLE_CENTER_X = 320.0
LANE_TIMEOUT = 0.35
LANE_LOST_SPEED = 30


def _in_closed(value, lo, hi):
    return value is not None and math.isfinite(value) and lo <= value <= hi


class MotionPlanningNode(Node):
    def __init__(self):
        super().__init__('motion_planner_node')

        self.sub_detection_topic = self.declare_parameter('sub_detection_topic', SUB_DETECTION_TOPIC_NAME).value
        self.sub_path_topic = self.declare_parameter('sub_lane_topic', SUB_PATH_TOPIC_NAME).value
        self.sub_traffic_light_topic = self.declare_parameter('sub_traffic_light_topic', SUB_TRAFFIC_LIGHT_TOPIC_NAME).value
        self.sub_lidar_obstacle_topic = self.declare_parameter('sub_lidar_obstacle_topic', SUB_LIDAR_OBSTACLE_TOPIC_NAME).value
        self.sub_lidar_lane1_min_topic = self.declare_parameter(
            'sub_lidar_lane1_min_topic', SUB_LIDAR_LANE1_MIN_TOPIC_NAME
        ).value
        self.sub_lane_control_topic = self.declare_parameter(
            'sub_lane_control_topic', SUB_LANE_CONTROL_TOPIC_NAME
        ).value
        self.sub_force_start_topic = self.declare_parameter('sub_force_start_topic', SUB_FORCE_START_TOPIC_NAME).value
        self.pub_topic = self.declare_parameter('pub_topic', PUB_TOPIC_NAME).value
        self.pub_finish_reason_topic = self.declare_parameter(
            'pub_finish_reason_topic', PUB_FINISH_REASON_TOPIC_NAME
        ).value

        self.timer_period = self.declare_parameter('timer', TIMER).value

        self.qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1
        )

        self.detection_data = None
        self.path_data = None
        self.traffic_light_data = None
        self.lidar_data = None
        self.lane1_min = None
        self.lane_center_x = None
        self.lane_mask_area = 0.0
        self.lane_control_stamp = None

        self.steering_command = 0
        self.left_speed_command = 0
        self.right_speed_command = 0
        self.filtered_steer = 0.0
        self.limited_steer = 0.0
        self.control_debug = 'init'

        self.declare_parameter('require_green_start', True)
        self.require_green_start = True
        self.started = False
        self.green_hits = 0
        self.need_green_hits = self.declare_parameter('need_green_hits', NEED_GREEN_HITS).value

        self.declare_parameter('enable_finish_stop', True)
        self.declare_parameter('need_finish_hits', NEED_FINISH_HITS)
        self.declare_parameter('lidar_stop_rmin', LIDAR_STOP_RMIN)
        self.declare_parameter('lidar_stop_rmax', LIDAR_STOP_RMAX)
        self.declare_parameter('use_lane_surface_control', True)
        self.declare_parameter('drive_speed', DRIVE_SPEED)
        self.declare_parameter('steer_max', STEER_MAX)
        self.declare_parameter('steer_k', STEER_K)
        self.declare_parameter('steer_alpha', STEER_ALPHA)
        self.declare_parameter('steer_rate', STEER_RATE)
        self.declare_parameter('vehicle_center_x', VEHICLE_CENTER_X)
        self.declare_parameter('lane_timeout', LANE_TIMEOUT)
        self.declare_parameter('lane_lost_speed', LANE_LOST_SPEED)

        self.finish_hits = 0

        self.detection_sub = self.create_subscription(
            DetectionArray, self.sub_detection_topic, self.detection_callback, self.qos_profile
        )
        self.path_sub = self.create_subscription(
            PathPlanningResult, self.sub_path_topic, self.path_callback, self.qos_profile
        )
        self.traffic_light_sub = self.create_subscription(
            String, self.sub_traffic_light_topic, self.traffic_light_callback, self.qos_profile
        )
        self.lidar_sub = self.create_subscription(
            Bool, self.sub_lidar_obstacle_topic, self.lidar_callback, self.qos_profile
        )
        self.lane1_min_sub = self.create_subscription(
            Float32, self.sub_lidar_lane1_min_topic, self.lane1_min_callback, self.qos_profile
        )
        self.lane_control_sub = self.create_subscription(
            Float32MultiArray,
            self.sub_lane_control_topic,
            self.lane_control_callback,
            self.qos_profile,
        )
        self.force_start_sub = self.create_subscription(
            Bool, self.sub_force_start_topic, self.force_start_callback, self.qos_profile
        )

        self.publisher = self.create_publisher(MotionCommand, self.pub_topic, self.qos_profile)
        self.reason_pub = self.create_publisher(String, self.pub_finish_reason_topic, self.qos_profile)
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

    def detection_callback(self, msg: DetectionArray):
        self.detection_data = msg

    def path_callback(self, msg: PathPlanningResult):
        self.path_data = list(zip(msg.x_points, msg.y_points))

    def traffic_light_callback(self, msg: String):
        self.traffic_light_data = msg

    def lidar_callback(self, msg: Bool):
        self.lidar_data = msg

    def lane1_min_callback(self, msg: Float32):
        self.lane1_min = float(msg.data)

    def lane_control_callback(self, msg: Float32MultiArray):
        if len(msg.data) < 2:
            return
        center_x = float(msg.data[0])
        self.lane_mask_area = float(msg.data[1])
        if math.isfinite(center_x):
            self.lane_center_x = center_x
            self.lane_control_stamp = self.get_clock().now()

    def force_start_callback(self, msg: Bool):
        if not msg.data:
            return
        self.started = True
        self.get_logger().warn('force_start: wait_green latch released')

    def _traffic_light_bbox(self):
        if self.detection_data is None:
            return None
        best = None
        best_area = -1.0
        for detection in self.detection_data.detections:
            if detection.class_name != 'traffic_light':
                continue
            xmin = detection.bbox.center.position.x - detection.bbox.size.x / 2.0
            xmax = detection.bbox.center.position.x + detection.bbox.size.x / 2.0
            ymin = detection.bbox.center.position.y - detection.bbox.size.y / 2.0
            ymax = detection.bbox.center.position.y + detection.bbox.size.y / 2.0
            area = detection.bbox.size.x * detection.bbox.size.y
            if area > best_area:
                best_area = area
                best = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
        return best

    def _zero_command(self):
        self.steering_command = 0
        self.left_speed_command = 0
        self.right_speed_command = 0
        self.filtered_steer = 0.0
        self.limited_steer = 0.0
        self.control_debug = 'stop_reset'

    def _publish(self):
        motion_command_msg = MotionCommand()
        motion_command_msg.steering = self.steering_command
        motion_command_msg.left_speed = self.left_speed_command
        motion_command_msg.right_speed = self.right_speed_command
        self.publisher.publish(motion_command_msg)

    def _publish_reason(self, reason: str):
        msg = String()
        msg.data = reason
        self.reason_pub.publish(msg)

    def _lidar_ok(self):
        rmin = float(self.get_parameter('lidar_stop_rmin').value)
        rmax = float(self.get_parameter('lidar_stop_rmax').value)
        return _in_closed(self.lane1_min, rmin, rmax)

    def _finish_source(self, bbox):
        """no_tl / none / lidar / off. 신호등 박스가 있을 때만 라이다 정지를 연다."""
        if not bool(self.get_parameter('enable_finish_stop').value):
            return 'off'
        if bbox is None:
            return 'no_tl'
        if self._lidar_ok():
            return 'lidar'
        return 'none'

    def timer_callback(self):
        self.require_green_start = bool(self.get_parameter('require_green_start').value)
        color = self.traffic_light_data.data if self.traffic_light_data is not None else 'None'

        if self.require_green_start and not self.started:
            if color == 'Green':
                self.green_hits += 1
                if self.green_hits >= self.need_green_hits:
                    self.started = True
            else:
                self.green_hits = 0
            if not self.started:
                self._zero_command()
                self.get_logger().info(
                    f"wait_green color={color} hits={self.green_hits} "
                    f"steering: {self.steering_command}, "
                    f"left_speed: {self.left_speed_command}, "
                    f"right_speed: {self.right_speed_command}"
                )
                self._publish_reason('wait_green')
                self._publish()
                return

        bbox = self._traffic_light_bbox()
        source = self._finish_source(bbox)
        finish_ok = source == 'lidar'
        need_hits = int(self.get_parameter('need_finish_hits').value)
        if finish_ok:
            self.finish_hits += 1
        else:
            self.finish_hits = 0

        front_min = self.lane1_min if self.lane1_min is not None else float('nan')
        has_tl = bbox is not None

        if finish_ok and self.finish_hits >= need_hits:
            self._zero_command()
            self.get_logger().info(
                f"lidar_stop tl=1 front_min={front_min:.3f} hits={self.finish_hits}/{need_hits} "
                f"steering: {self.steering_command}, "
                f"left_speed: {self.left_speed_command}, "
                f"right_speed: {self.right_speed_command}"
            )
            self._publish_reason(source)
            self._publish()
            return

        self._follow_path()
        self.get_logger().info(
            f"steering: {self.steering_command}, "
            f"left_speed: {self.left_speed_command}, "
            f"right_speed: {self.right_speed_command} "
            f"hits={self.finish_hits}/{need_hits} "
            f"src={source} tl={int(has_tl)} front_min={front_min:.3f} "
            f"{self.control_debug}"
        )
        self._publish_reason(source)
        self._publish()

    def _follow_path(self):
        drive_speed = int(self.get_parameter('drive_speed').value)
        if bool(self.get_parameter('use_lane_surface_control').value):
            if self._lane_control_is_fresh():
                self._follow_lane_surface()
                self.left_speed_command = drive_speed
                self.right_speed_command = drive_speed
                return

            lane_lost_speed = int(self.get_parameter('lane_lost_speed').value)
            self.filtered_steer = 0.0
            self.limited_steer = 0.0
            self.steering_command = 0
            self.left_speed_command = lane_lost_speed
            self.right_speed_command = lane_lost_speed
            self.control_debug = (
                f"ctrl=lane_lost center={self.lane_center_x} "
                f"area={self.lane_mask_area:.0f}"
            )
            return

        if self.path_data is None:
            self.steering_command = 0
            self.control_debug = 'ctrl=bang no_path'
        else:
            target_slope = DMFL.calculate_slope_between_points(self.path_data[-10], self.path_data[-1])
            if target_slope > 0:
                self.steering_command = int(self.get_parameter('steer_max').value)
            elif target_slope < 0:
                self.steering_command = -int(self.get_parameter('steer_max').value)
            else:
                self.steering_command = 0
            self.control_debug = f'ctrl=bang slope={target_slope:.2f}'
        self.left_speed_command = drive_speed
        self.right_speed_command = drive_speed

    def _lane_control_is_fresh(self):
        if self.lane_center_x is None or self.lane_control_stamp is None:
            return False
        timeout = float(self.get_parameter('lane_timeout').value)
        age = (self.get_clock().now() - self.lane_control_stamp).nanoseconds * 1e-9
        return age <= timeout

    def _follow_lane_surface(self):
        center_x = float(self.lane_center_x)
        vehicle_center_x = float(self.get_parameter('vehicle_center_x').value)
        steer_k = float(self.get_parameter('steer_k').value)
        steer_max = float(self.get_parameter('steer_max').value)
        alpha = float(self.get_parameter('steer_alpha').value)
        rate = float(self.get_parameter('steer_rate').value)

        alpha = min(max(alpha, 0.0), 1.0)
        rate = max(rate, 0.0)
        error_px = center_x - vehicle_center_x
        raw_steer = min(max(steer_k * error_px, -steer_max), steer_max)
        self.filtered_steer = (
            (1.0 - alpha) * self.filtered_steer + alpha * raw_steer
        )
        delta = min(
            max(self.filtered_steer - self.limited_steer, -rate),
            rate,
        )
        self.limited_steer = min(
            max(self.limited_steer + delta, -steer_max),
            steer_max,
        )
        self.steering_command = int(round(self.limited_steer))
        self.control_debug = (
            f"ctrl=surface center={center_x:.1f} area={self.lane_mask_area:.0f} "
            f"err={error_px:.1f} raw={raw_steer:.2f} "
            f"ema={self.filtered_steer:.2f} limited={self.limited_steer:.2f}"
        )


def main(args=None):
    install_shutdown()
    rclpy.init(args=args)
    node = MotionPlanningNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        print("\n\nshutdown\n\n")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
