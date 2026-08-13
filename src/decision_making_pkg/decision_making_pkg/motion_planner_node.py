import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSReliabilityPolicy

from std_msgs.msg import String, Bool
from interfaces_pkg.msg import PathPlanningResult, DetectionArray, MotionCommand
from .lib import decision_making_func_lib as DMFL

#---------------Variable Setting---------------
SUB_DETECTION_TOPIC_NAME = "detections"
SUB_PATH_TOPIC_NAME = "path_planning_result"
SUB_TRAFFIC_LIGHT_TOPIC_NAME = "yolov8_traffic_light_info"
SUB_LIDAR_OBSTACLE_TOPIC_NAME = "lidar_obstacle_info"
PUB_TOPIC_NAME = "topic_control_signal"

# 저속 첫 주행 기본값 (launch: drive_speed:= / steer_max:= 로 덮어쓰기)
# 문서: docs/team/lowspeed-tuning.md
DEFAULT_DRIVE_SPEED = 60   # 0~255, 기본 속도
DEFAULT_STEER_MAX = 7      # driving.ino MAX_STEERING_STEP 과 일치
DEFAULT_MAX_SLOPE_ANGLE = 35.0  # steer_max에 해당하는 경로 기울기 각도(도)
DEFAULT_SLOPE_DEADBAND = 2.0    # 이 각도 미만은 직진(조향 0) 사불감대
DEFAULT_STRAIGHT_STEER_THRESHOLD = 1 # 조향 크기(절대값)이 이 이하일 때 직진 속도 적용
#----------------------------------------------

# 모션 플랜 발행 주기 (초) - 소수점 필요 (int형은 반영되지 않음)
TIMER = 0.1

class MotionPlanningNode(Node):
    def __init__(self):
        super().__init__('motion_planner_node')

        # 토픽 이름 설정
        self.sub_detection_topic = self.declare_parameter('sub_detection_topic', SUB_DETECTION_TOPIC_NAME).value
        self.sub_path_topic = self.declare_parameter('sub_lane_topic', SUB_PATH_TOPIC_NAME).value
        self.sub_traffic_light_topic = self.declare_parameter('sub_traffic_light_topic', SUB_TRAFFIC_LIGHT_TOPIC_NAME).value
        self.sub_lidar_obstacle_topic = self.declare_parameter('sub_lidar_obstacle_topic', SUB_LIDAR_OBSTACLE_TOPIC_NAME).value
        self.pub_topic = self.declare_parameter('pub_topic', PUB_TOPIC_NAME).value

        self.timer_period = self.declare_parameter('timer', TIMER).value
        self.drive_speed = int(self.declare_parameter('drive_speed', DEFAULT_DRIVE_SPEED).value)
        self.steer_max = int(self.declare_parameter('steer_max', DEFAULT_STEER_MAX).value)
        self.drive_speed_straight = int(self.declare_parameter('drive_speed_straight', self.drive_speed + 15).value)
        self.drive_speed_corner = int(self.declare_parameter('drive_speed_corner', max(20, self.drive_speed - 15)).value)
        self.max_slope_angle = float(self.declare_parameter('max_slope_angle', DEFAULT_MAX_SLOPE_ANGLE).value)
        self.slope_deadband = float(self.declare_parameter('slope_deadband', DEFAULT_SLOPE_DEADBAND).value)
        self.straight_steer_threshold = int(self.declare_parameter('straight_steer_threshold', DEFAULT_STRAIGHT_STEER_THRESHOLD).value)

        # QoS 설정
        self.qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1
        )

        # 변수 초기화
        self.detection_data = None
        self.path_data = None
        self.traffic_light_data = None
        self.lidar_data = None

        self.steering_command = 0
        self.left_speed_command = 0
        self.right_speed_command = 0
        

        # 서브스크라이버 설정
        self.detection_sub = self.create_subscription(DetectionArray, self.sub_detection_topic, self.detection_callback, self.qos_profile)
        self.path_sub = self.create_subscription(PathPlanningResult, self.sub_path_topic, self.path_callback, self.qos_profile)
        self.traffic_light_sub = self.create_subscription(String, self.sub_traffic_light_topic, self.traffic_light_callback, self.qos_profile)
        self.lidar_sub = self.create_subscription(Bool, self.sub_lidar_obstacle_topic, self.lidar_callback, self.qos_profile)

        # 퍼블리셔 설정
        self.publisher = self.create_publisher(MotionCommand, self.pub_topic, self.qos_profile)
        self.debug_pub = self.create_publisher(String, 'control_debug', self.qos_profile)
        self._last_reason = 'init'

        # 타이머 설정
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        self.get_logger().info(
            f'drive_speed={self.drive_speed} (straight={self.drive_speed_straight}, corner={self.drive_speed_corner}), steer_max={self.steer_max}'
        )

    def detection_callback(self, msg: DetectionArray):
        self.detection_data = msg

    def path_callback(self, msg: PathPlanningResult):
        self.path_data = list(zip(msg.x_points, msg.y_points))
                
    def traffic_light_callback(self, msg: String):
        self.traffic_light_data = msg

    def lidar_callback(self, msg: Bool):
        self.lidar_data = msg
        
    def timer_callback(self):

        if self.lidar_data is not None and self.lidar_data.data is True:
            # 라이다가 장애물을 감지한 경우
            self.steering_command = 0 
            self.left_speed_command = 0 
            self.right_speed_command = 0 
            self._last_reason = 'lidar_stop'

        elif self.traffic_light_data is not None and self.traffic_light_data.data == 'Red':
            # 빨간색 신호등을 감지한 경우
            for detection in self.detection_data.detections:
                if detection.class_name=='traffic_light':
                    x_min = int(detection.bbox.center.position.x - detection.bbox.size.x / 2) # bbox의 좌측상단 꼭짓점 x좌표
                    x_max = int(detection.bbox.center.position.x + detection.bbox.size.x / 2) # bbox의 우측하단 꼭짓점 x좌표
                    y_min = int(detection.bbox.center.position.y - detection.bbox.size.y / 2) # bbox의 좌측상단 꼭짓점 y좌표
                    y_max = int(detection.bbox.center.position.y + detection.bbox.size.y / 2) # bbox의 우측하단 꼭짓점 y좌표

                    if y_max < 150:
                        # 신호등 위치에 따른 정지명령 결정
                        self.steering_command = 0 
                        self.left_speed_command = 0 
                        self.right_speed_command = 0
                        self._last_reason = 'red_stop'
        else:
            if self.path_data is None:
                self.steering_command = 0
                self._last_reason = 'no_path'
                calculated_speed = self.drive_speed
            else:
                target_slope = DMFL.calculate_slope_between_points(self.path_data[-10], self.path_data[-1])
                
                if target_slope == 'inf':
                    self.steering_command = 0
                    self._last_reason = 'path slope=inf'
                else:
                    abs_slope = abs(target_slope)
                    if abs_slope < self.slope_deadband:
                        self.steering_command = 0
                    else:
                        # 기울기에 비례하여 부드럽게 [-steer_max, +steer_max] 범위로 양자화
                        steer_float = (target_slope / self.max_slope_angle) * self.steer_max
                        clamped_steer = max(-self.steer_max, min(self.steer_max, round(steer_float)))
                        self.steering_command = int(clamped_steer)
                    self._last_reason = f'path slope={target_slope:.2f}'

                # 직진/곡선 조향각에 따른 속도 가감속 로직
                abs_steer = abs(self.steering_command)
                if abs_steer <= self.straight_steer_threshold:
                    calculated_speed = self.drive_speed_straight
                else:
                    steer_ratio = (abs_steer - self.straight_steer_threshold) / max(1, (self.steer_max - self.straight_steer_threshold))
                    calculated_speed = int(self.drive_speed_straight - steer_ratio * (self.drive_speed_straight - self.drive_speed_corner))
                    calculated_speed = max(self.drive_speed_corner, min(self.drive_speed_straight, calculated_speed))

            self.left_speed_command = calculated_speed
            self.right_speed_command = calculated_speed



        self.get_logger().info(f"steering: {self.steering_command}, " 
                               f"left_speed: {self.left_speed_command}, " 
                               f"right_speed: {self.right_speed_command}")

        # 모션 명령 메시지 생성 및 퍼블리시
        motion_command_msg = MotionCommand()
        motion_command_msg.steering = self.steering_command
        motion_command_msg.left_speed = self.left_speed_command
        motion_command_msg.right_speed = self.right_speed_command
        self.publisher.publish(motion_command_msg)
        dbg = String()
        tl = self.traffic_light_data.data if self.traffic_light_data is not None else 'none'
        lidar = int(bool(self.lidar_data.data)) if self.lidar_data is not None else -1
        dbg.data = (
            f"reason={self._last_reason} steer={self.steering_command} "
            f"L={self.left_speed_command} R={self.right_speed_command} tl={tl} lidar={lidar}"
        )
        self.debug_pub.publish(dbg)

def main(args=None):
    rclpy.init(args=args)
    node = MotionPlanningNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\n\nshutdown\n\n")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
