from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """
    실차 폐루프 launch (모터 ON).

    소단위 검증은 먼저:
      ros2 launch launch_pkg camera_only.launch.py
      ros2 launch launch_pkg perception_debug.launch.py   # serial 없음
      ros2 launch launch_pkg lidar_debug.launch.py
      ros2 launch launch_pkg debug_overlay.launch.py      # 이 launch 위에 HUD
    문서: docs/team/debug-and-incremental-test.md

    활성화 단계:
      1) 카메라 + YOLO + lane + path + motion + serial  ← 기본
      2) traffic_light_detector 주석 해제
      3) lidar_* 3노드 주석 해제

    예:
      ros2 launch launch_pkg main.launch.py model:=.../teamop_best.pt device:=cuda:0 drive_speed:=50
    """
    model = LaunchConfiguration("model")
    device = LaunchConfiguration("device")
    threshold = LaunchConfiguration("threshold")
    drive_speed = LaunchConfiguration("drive_speed")
    steer_max = LaunchConfiguration("steer_max")
    data_source = LaunchConfiguration("data_source")
    cam_num = LaunchConfiguration("cam_num")

    src_args = []
    src_params = {}
    for name, default in (
        ("src0_x", "238"),
        ("src0_y", "316"),
        ("src1_x", "402"),
        ("src1_y", "313"),
        ("src2_x", "501"),
        ("src2_y", "476"),
        ("src3_x", "155"),
        ("src3_y", "476"),
        ("cutting_idx", "300"),
    ):
        src_args.append(DeclareLaunchArgument(name, default_value=default))
        src_params[name] = ParameterValue(LaunchConfiguration(name), value_type=int)

    return LaunchDescription([
        DeclareLaunchArgument(
            "model",
            default_value="yolov8m.pt",
            description="YOLO weights path. Use weights/teamop_best.pt on the car.",
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
        DeclareLaunchArgument(
            "data_source",
            default_value="camera",
            description="image_publisher: camera | video | image",
        ),
        DeclareLaunchArgument("cam_num", default_value="0"),
        *src_args,

        Node(
            package="camera_perception_pkg",
            executable="image_publisher_node",
            name="image_publisher_node",
            output="screen",
            parameters=[{
                "data_source": data_source,
                "cam_num": ParameterValue(cam_num, value_type=int),
                "logger": False,
            }],
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
            parameters=[src_params],
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

        Node(
            package="serial_communication_pkg",
            executable="serial_sender_node",
            name="serial_sender_node",
            output="screen",
        ),
    ])
