from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """라이다 3노드 + top-down 시각화. 보넷 장착 정렬용."""
    scan_topic = LaunchConfiguration("scan_topic")
    show_image = LaunchConfiguration("show_image")

    return LaunchDescription([
        DeclareLaunchArgument("scan_topic", default_value="lidar_raw"),
        DeclareLaunchArgument("show_image", default_value="true"),
        Node(
            package="lidar_perception_pkg",
            executable="lidar_publisher_node",
            name="lidar_publisher_node",
            output="screen",
        ),
        Node(
            package="lidar_perception_pkg",
            executable="lidar_processor_node",
            name="lidar_processor_node",
            output="screen",
        ),
        Node(
            package="lidar_perception_pkg",
            executable="lidar_obstacle_detector_node",
            name="lidar_obstacle_detector_node",
            output="screen",
        ),
        Node(
            package="debug_pkg",
            executable="lidar_scan_visualizer_node",
            name="lidar_scan_visualizer_node",
            output="screen",
            parameters=[{
                "scan_topic": scan_topic,
                "show_image": ParameterValue(show_image, value_type=bool),
            }],
        ),
    ])
