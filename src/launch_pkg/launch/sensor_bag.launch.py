"""센서만 켜고 ros2 bag 기록. 주행(시리얼·모션) 없음.

기존 launch/노드 파일을 수정하지 않는다. Ctrl+C 로 bag 을 닫는다.

  ros2 launch launch_pkg sensor_bag.launch.py
  ros2 launch launch_pkg sensor_bag.launch.py cam_num:=2 lidar:=true
  ros2 launch launch_pkg sensor_bag.launch.py lidar:=false
  ros2 launch launch_pkg sensor_bag.launch.py processed:=true   # lidar_processed + obstacle 도 기록

재생:
  ros2 bag play <bags/sensor_YYYYMMDD_HHMMSS>
"""
from datetime import datetime
from pathlib import Path
import sys

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    LogInfo,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

_LAUNCH_DIR = str(Path(__file__).resolve().parent)
if _LAUNCH_DIR not in sys.path:
    sys.path.insert(0, _LAUNCH_DIR)
from workspace_paths import workspace_root  # noqa: E402


def _truthy(text: str) -> bool:
    return text.strip().lower() in ('1', 'true', 'yes', 'on')


def _start_bag(context, *args, **kwargs):
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    bag_dir = LaunchConfiguration('bag_dir').perform(context).strip()
    if not bag_dir:
        bag_dir = str(workspace_root() / 'bags')
    Path(bag_dir).mkdir(parents=True, exist_ok=True)
    bag_path = str(Path(bag_dir) / f'sensor_{stamp}')

    topics = ['/image_raw']
    if _truthy(LaunchConfiguration('lidar').perform(context)):
        topics.extend(['/lidar_raw', '/tf'])
        if _truthy(LaunchConfiguration('processed').perform(context)):
            topics.extend(['/lidar_processed', '/lidar_obstacle_info'])

    cmd = [
        'ros2', 'bag', 'record',
        '--include-unpublished-topics',
        '-o', bag_path,
        *topics,
    ]
    return [
        LogInfo(msg=f'[sensor_bag] recording -> {bag_path}'),
        LogInfo(msg='[sensor_bag] topics: ' + ' '.join(topics)),
        LogInfo(msg='[sensor_bag] no serial / motion. stop with Ctrl+C'),
        ExecuteProcess(cmd=cmd, output='screen', name='sensor_bag_record'),
    ]


def generate_launch_description():
    cam_num = LaunchConfiguration('cam_num')
    show_image = LaunchConfiguration('show_image')
    lidar = LaunchConfiguration('lidar')
    processed = LaunchConfiguration('processed')

    return LaunchDescription([
        DeclareLaunchArgument(
            'cam_num',
            default_value='2',
            description='OpenCV camera index (/dev/videoN). C920 is usually 2',
        ),
        DeclareLaunchArgument(
            'show_image',
            default_value='true',
            description='Camera preview window (image_publisher logger)',
        ),
        DeclareLaunchArgument(
            'lidar',
            default_value='true',
            description='Start lidar_publisher and record /lidar_raw',
        ),
        DeclareLaunchArgument(
            'processed',
            default_value='false',
            description='Also run lidar processor/obstacle and record those topics',
        ),
        DeclareLaunchArgument(
            'bag_dir',
            default_value='',
            description='Bag parent directory (default: <ros2_ws>/bags)',
        ),
        Node(
            package='camera_perception_pkg',
            executable='image_publisher_node',
            name='image_publisher_node',
            output='screen',
            parameters=[{
                'data_source': 'camera',
                'cam_num': ParameterValue(cam_num, value_type=int),
                'logger': ParameterValue(show_image, value_type=bool),
            }],
        ),
        Node(
            package='lidar_perception_pkg',
            executable='lidar_publisher_node',
            name='lidar_publisher_node',
            output='screen',
            condition=IfCondition(lidar),
        ),
        Node(
            package='lidar_perception_pkg',
            executable='lidar_processor_node',
            name='lidar_processor_node',
            output='screen',
            condition=IfCondition(processed),
        ),
        Node(
            package='lidar_perception_pkg',
            executable='lidar_obstacle_detector_node',
            name='lidar_obstacle_detector_node',
            output='screen',
            condition=IfCondition(processed),
        ),
        OpaqueFunction(function=_start_bag),
    ])
