from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """카메라만. 모터/YOLO 없음. 문서: docs/team/debug-and-incremental-test.md"""
    cam_num = LaunchConfiguration("cam_num")
    logger = LaunchConfiguration("logger")

    return LaunchDescription([
        DeclareLaunchArgument("cam_num", default_value="0"),
        DeclareLaunchArgument(
            "logger",
            default_value="true",
            description="imshow Camera Image",
        ),
        Node(
            package="camera_perception_pkg",
            executable="image_publisher_node",
            name="image_publisher_node",
            output="screen",
            parameters=[{
                "data_source": "camera",
                "cam_num": ParameterValue(cam_num, value_type=int),
                "logger": ParameterValue(logger, value_type=bool),
            }],
        ),
    ])
