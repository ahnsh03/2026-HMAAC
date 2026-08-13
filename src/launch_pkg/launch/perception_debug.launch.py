import sys
from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

_LAUNCH_DIR = str(Path(__file__).resolve().parent)
if _LAUNCH_DIR not in sys.path:
    sys.path.insert(0, _LAUNCH_DIR)
from workspace_paths import default_yolo_weights  # noqa: E402


def generate_launch_description():
    """Stage 3: 인지 A/B. serial/motion 없음.

    IPM은 Stage 2에서 맞춘 src* 를 그대로 넘긴다. 가중치만 바꾼다.
    """
    model = LaunchConfiguration("model")
    device = LaunchConfiguration("device")
    threshold = LaunchConfiguration("threshold")
    cam_num = LaunchConfiguration("cam_num")
    show_image = LaunchConfiguration("show_image")

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
        DeclareLaunchArgument("model", default_value=default_yolo_weights()),
        DeclareLaunchArgument("device", default_value="cuda:0"),
        DeclareLaunchArgument("threshold", default_value="0.5"),
        DeclareLaunchArgument("cam_num", default_value="0"),
        DeclareLaunchArgument("show_image", default_value="true"),
        *src_args,
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
            parameters=[{
                "show_image": ParameterValue(show_image, value_type=bool),
                **src_params,
            }],
        ),
        Node(
            package="debug_pkg",
            executable="yolov8_visualizer_node",
            name="yolov8_visualizer_node",
            output="screen",
        ),
        Node(
            package="decision_making_pkg",
            executable="path_planner_node",
            name="path_planner_node",
            output="screen",
        ),
        Node(
            package="debug_pkg",
            executable="path_visualizer_node",
            name="path_visualizer_node",
            output="screen",
        ),
    ])
