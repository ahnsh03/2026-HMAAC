from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Stage 1: 카메라만. 모터/YOLO 없음."""
    cam_num = LaunchConfiguration("cam_num")

    return LaunchDescription([
        DeclareLaunchArgument("cam_num", default_value="0"),
        Node(
            package="camera_perception_pkg",
            executable="image_publisher_node",
            name="image_publisher_node",
            output="screen",
            parameters=[{
                "data_source": "camera",
                "cam_num": ParameterValue(cam_num, value_type=int),
                "logger": True,
            }],
        ),
    ])
