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
SUB_FORCE_START_TOPIC_NAME = "force_start"
PUB_TOPIC_NAME = "topic_control_signal"

#----------------------------------------------

# 모션 플랜 발행 주기 (초) - 소수점 필요 (int형은 반영되지 않음)
TIMER = 0.1
# 출발 게이트: 연속 Green 횟수 (0.1s × 3 = 0.3s)
NEED_GREEN_HITS = 3

class MotionPlanningNode(Node):
    def __init__(self):
        super().__init__('motion_planner_node')

        # 토픽 이름 설정
        self.sub_detection_topic = self.declare_parameter('sub_detection_topic', SUB_DETECTION_TOPIC_NAME).value
        self.sub_path_topic = self.declare_parameter('sub_lane_topic', SUB_PATH_TOPIC_NAME).value
        self.sub_traffic_light_topic = self.declare_parameter('sub_traffic_light_topic', SUB_TRAFFIC_LIGHT_TOPIC_NAME).value
        self.sub_lidar_obstacle_topic = self.declare_parameter('sub_lidar_obstacle_topic', SUB_LIDAR_OBSTACLE_TOPIC_NAME).value
        self.sub_force_start_topic = self.declare_parameter('sub_force_start_topic', SUB_FORCE_START_TOPIC_NAME).value
        self.pub_topic = self.declare_parameter('pub_topic', PUB_TOPIC_NAME).value
        
        self.timer_period = self.declare_parameter('timer', TIMER).value

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

        # 간략 미션: 첫 Green만 보고 출발. 한 번 출발하면 되돌리지 않음.
        # require_green_start는 매 주기 get_parameter (ros2 param set 로 구간 테스트 가능).
        self.declare_parameter('require_green_start', True)
        self.require_green_start = True
        self.started = False
        self.green_hits = 0
        self.need_green_hits = self.declare_parameter('need_green_hits', NEED_GREEN_HITS).value
        

        # 서브스크라이버 설정
        self.detection_sub = self.create_subscription(DetectionArray, self.sub_detection_topic, self.detection_callback, self.qos_profile)
        self.path_sub = self.create_subscription(PathPlanningResult, self.sub_path_topic, self.path_callback, self.qos_profile)
        self.traffic_light_sub = self.create_subscription(String, self.sub_traffic_light_topic, self.traffic_light_callback, self.qos_profile)
        self.lidar_sub = self.create_subscription(Bool, self.sub_lidar_obstacle_topic, self.lidar_callback, self.qos_profile)
        self.force_start_sub = self.create_subscription(Bool, self.sub_force_start_topic, self.force_start_callback, self.qos_profile)

        # 퍼블리셔 설정
        self.publisher = self.create_publisher(MotionCommand, self.pub_topic, self.qos_profile)

        # 타이머 설정
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

    def detection_callback(self, msg: DetectionArray):
        self.detection_data = msg

    def path_callback(self, msg: PathPlanningResult):
        self.path_data = list(zip(msg.x_points, msg.y_points))
                
    def traffic_light_callback(self, msg: String):
        self.traffic_light_data = msg

    def lidar_callback(self, msg: Bool):
        self.lidar_data = msg

    def force_start_callback(self, msg: Bool):
        if not msg.data:
            return
        self.started = True
        self.get_logger().warn('force_start: wait_green latch released')
        
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
                self.steering_command = 0
                self.left_speed_command = 0
                self.right_speed_command = 0
                self.get_logger().info(
                    f"wait_green color={color} hits={self.green_hits} "
                    f"steering: {self.steering_command}, "
                    f"left_speed: {self.left_speed_command}, "
                    f"right_speed: {self.right_speed_command}"
                )
                motion_command_msg = MotionCommand()
                motion_command_msg.steering = self.steering_command
                motion_command_msg.left_speed = self.left_speed_command
                motion_command_msg.right_speed = self.right_speed_command
                self.publisher.publish(motion_command_msg)
                return

        if self.lidar_data is not None and self.lidar_data.data is True:
            # 라이다가 장애물을 감지한 경우
            self.steering_command = 0 
            self.left_speed_command = 0 
            self.right_speed_command = 0 

        elif (
            not self.require_green_start
            and self.traffic_light_data is not None
            and self.traffic_light_data.data == 'Red'
            and self.detection_data is not None
        ):
            # require_green_start=False 일 때만 기존 적색 근접 정지.
            # 간략 미션(래치 ON)에서는 출발 후 이 분기를 타지 않음.
            for detection in self.detection_data.detections:
                if detection.class_name == 'traffic_light':
                    # bbox 박스 정보 모두 남겨둠 (x_min, x_max, y_min, y_max)
                    x_min = int(detection.bbox.center.position.x - detection.bbox.size.x / 2)
                    x_max = int(detection.bbox.center.position.x + detection.bbox.size.x / 2)
                    y_min = int(detection.bbox.center.position.y - detection.bbox.size.y / 2)
                    y_max = int(detection.bbox.center.position.y + detection.bbox.size.y / 2)
         

                    if y_max < 150:
                        # 신호등 위치에 따른 정지명령 결정
                        self.steering_command = 0 
                        self.left_speed_command = 0 
                        self.right_speed_command = 0
        else:
            if self.path_data is None:
                self.steering_command = 0
            else:
                target_slope = DMFL.calculate_slope_between_points(self.path_data[-10], self.path_data[-1])
                
                if target_slope > 0:
                    self.steering_command =  7 # 예시 조향 값 (7이 최대 조향) 
                elif target_slope < 0:
                    self.steering_command =  -7
                else:
                    self.steering_command = 0


            self.left_speed_command = 70  # 예시 속도 값 (255가 최대 속도)
            self.right_speed_command = 70  # 예시 속도 값 (255가 최대 속도)



        self.get_logger().info(f"steering: {self.steering_command}, " 
                               f"left_speed: {self.left_speed_command}, " 
                               f"right_speed: {self.right_speed_command}")

        # 모션 명령 메시지 생성 및 퍼블리시
        motion_command_msg = MotionCommand()
        motion_command_msg.steering = self.steering_command
        motion_command_msg.left_speed = self.left_speed_command
        motion_command_msg.right_speed = self.right_speed_command
        self.publisher.publish(motion_command_msg)

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
