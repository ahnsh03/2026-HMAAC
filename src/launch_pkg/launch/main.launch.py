from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import sys
from pathlib import Path

_LAUNCH_DIR = str(Path(__file__).resolve().parent)
if _LAUNCH_DIR not in sys.path:
    sys.path.insert(0, _LAUNCH_DIR)
from workspace_paths import default_yolo_weights  # noqa: E402


def generate_launch_description():
    model = LaunchConfiguration('model')

    return LaunchDescription([
        DeclareLaunchArgument(
            'model',
            default_value=default_yolo_weights(),
            description='YOLO weights path (absolute; default: ros2_ws/best.pt)',
        ),
        DeclareLaunchArgument(
            'debug',
            default_value='true',
            description='YOLO/path OpenCV debug visualizer nodes',
        ),
        DeclareLaunchArgument(
            'require_green_start',
            default_value='true',
            description='Wait for Green (or /force_start) before driving. false = section test, drive immediately',
        ),
        Node(
            package='camera_perception_pkg',
            executable='image_publisher_node',
            name='image_publisher_node',
            output='screen'
        ),
        Node(
            package='camera_perception_pkg',
            executable='yolov8_node',
            name='yolov8_node',
            output='screen',
            parameters=[{'model': model}],
        ),
        Node(
            package='camera_perception_pkg',
            executable='lane_info_extractor_node',
            name='lane_info_extractor_node',
            output='screen'
        ),
        Node(
            package='camera_perception_pkg',
            executable='traffic_light_detector_node',
            name='traffic_light_detector_node',
            output='screen',
        ),
        Node(
            package='lidar_perception_pkg',
            executable='lidar_publisher_node',
            name='lidar_publisher_node',
            output='screen',
        ),
        Node(
            package='lidar_perception_pkg',
            executable='lidar_processor_node',
            name='lidar_processor_node',
            output='screen',
        ),
        Node(
            package='lidar_perception_pkg',
            executable='lidar_obstacle_detector_node',
            name='lidar_obstacle_detector_node',
            output='screen',
        ),
        Node(
            package='decision_making_pkg',
            executable='motion_planner_node',
            name='motion_planner_node',
            output='screen',
            parameters=[{
                'require_green_start': ParameterValue(
                    LaunchConfiguration('require_green_start'), value_type=bool
                ),
            }],
        ),
        Node(
            package='decision_making_pkg',
            executable='path_planner_node',
            name='path_planner_node',
            output='screen'
        ),
        Node(
            package='serial_communication_pkg',
            executable='serial_sender_node',
            name='serial_sender_node',
            output='screen',
        ),
        Node(
            package='debug_pkg',
            executable='yolov8_visualizer_node',
            name='yolov8_visualizer_node',
            output='screen',
            condition=IfCondition(LaunchConfiguration('debug')),
        ),
        Node(
            package='debug_pkg',
            executable='path_visualizer_node',
            name='path_visualizer_node',
            output='screen',
            condition=IfCondition(LaunchConfiguration('debug')),
        ),
    ])
