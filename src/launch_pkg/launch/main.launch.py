from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """
    실차 main launch.

    활성화 단계 (docs/team/repo-structure-and-realcar-guide.md):
      1) 카메라 + YOLO + lane + path + motion + serial  ← 기본(저속 차선 추종)
      2) traffic_light_detector 주석 해제               ← 초록 후 출발
      3) lidar_* 3노드 주석 해제                        ← 종료 물체 정지 등

    예:
      ros2 launch launch_pkg main.launch.py
      ros2 launch launch_pkg main.launch.py model:=best.pt device:=cuda:0
      ros2 launch launch_pkg main.launch.py model:=best.pt drive_speed:=50
    """
    model = LaunchConfiguration("model")
    device = LaunchConfiguration("device")
    threshold = LaunchConfiguration("threshold")
    drive_speed = LaunchConfiguration("drive_speed")
    steer_max = LaunchConfiguration("steer_max")

    return LaunchDescription([
        DeclareLaunchArgument(
            "model",
            default_value="yolov8m.pt",
            description="YOLO weights path/name. Use best.pt after training.",
        ),
        DeclareLaunchArgument(
            "device",
            default_value="cpu",
            description="Inference device: cpu or cuda:0",
        ),
        DeclareLaunchArgument(
            "threshold",
            default_value="0.5",
            description="YOLO confidence threshold",
        ),
        DeclareLaunchArgument(
            "drive_speed",
            default_value="60",
            description="Left/right wheel PWM for low-speed first runs (0-255)",
        ),
        DeclareLaunchArgument(
            "steer_max",
            default_value="7",
            description="Max steering command magnitude (match MAX_STEERING_STEP)",
        ),

        # --- Stage 1: perception + planning + serial ---
        Node(
            package="camera_perception_pkg",
            executable="image_publisher_node",
            name="image_publisher_node",
            output="screen",
        ),
        Node(
            package="camera_perception_pkg",
            executable="yolov8_node",
            name="yolov8_node",
            output="screen",
            parameters=[{
                "model": model,
                "device": device,
                "threshold": ParameterValue(threshold, value_type=float),
            }],
        ),
        Node(
            package="camera_perception_pkg",
            executable="lane_info_extractor_node",
            name="lane_info_extractor_node",
            output="screen",
        ),

        # --- Stage 2: 신호등 (초록 후 출발) — 미션 단계에서 주석 해제 ---
        # Node(
        #     package='camera_perception_pkg',
        #     executable='traffic_light_detector_node',
        #     name='traffic_light_detector_node',
        #     output='screen'
        # ),

        # --- Stage 3: 라이다 (종료 물체 정지 등) — 미션 단계에서 주석 해제 ---
        # Node(
        #     package='lidar_perception_pkg',
        #     executable='lidar_publisher_node',
        #     name='lidar_publisher_node',
        #     output='screen'
        # ),
        # Node(
        #     package='lidar_perception_pkg',
        #     executable='lidar_processor_node',
        #     name='lidar_processor_node',
        #     output='screen'
        # ),
        # Node(
        #     package='lidar_perception_pkg',
        #     executable='lidar_obstacle_detector_node',
        #     name='lidar_obstacle_detector_node',
        #     output='screen'
        # ),

        Node(
            package="decision_making_pkg",
            executable="path_planner_node",
            name="path_planner_node",
            output="screen",
        ),
        Node(
            package="decision_making_pkg",
            executable="motion_planner_node",
            name="motion_planner_node",
            output="screen",
            parameters=[{
                "drive_speed": ParameterValue(drive_speed, value_type=int),
                "steer_max": ParameterValue(steer_max, value_type=int),
            }],
        ),

        # 실차 액추에이터 브리지 (Arduino IDE 시리얼 모니터와 동시 사용 금지)
        Node(
            package="serial_communication_pkg",
            executable="serial_sender_node",
            name="serial_sender_node",
            output="screen",
        ),
    ])
