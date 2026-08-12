from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """이미 떠 있는 파이프라인에 시각화만 붙인다 (main.launch 와 함께)."""
    show_image = LaunchConfiguration("show_image")

    return LaunchDescription([
        DeclareLaunchArgument("show_image", default_value="true"),
        Node(
            package="debug_pkg",
            executable="yolov8_visualizer_node",
            name="yolov8_visualizer_node",
            output="screen",
        ),
        Node(
            package="debug_pkg",
            executable="path_visualizer_node",
            name="path_visualizer_node",
            output="screen",
        ),
        Node(
            package="debug_pkg",
            executable="control_hud_node",
            name="control_hud_node",
            output="screen",
            parameters=[{
                "show_image": ParameterValue(show_image, value_type=bool),
            }],
        ),
        Node(
            package="debug_pkg",
            executable="marker_node",
            name="marker_node",
            output="screen",
        ),
    ])
