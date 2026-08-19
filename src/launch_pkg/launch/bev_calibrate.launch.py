from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Stage 2: 카메라 이미지로 IPM 사다리꼴을 맞춘다. YOLO 없음.

    창에서 사다리꼴을 2차로 노면에 맞추고 p 로 숫자를 복사한다.
    """
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
                "logger": False,
            }],
        ),
        Node(
            package="debug_pkg",
            executable="bev_calibrator_node",
            name="bev_calibrator_node",
            output="screen",
        ),
    ])
