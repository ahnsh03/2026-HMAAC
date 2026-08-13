from datetime import datetime
from pathlib import Path
import sys

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnShutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

_LAUNCH_DIR = str(Path(__file__).resolve().parent)
if _LAUNCH_DIR not in sys.path:
    sys.path.insert(0, _LAUNCH_DIR)
from workspace_paths import default_yolo_weights, workspace_root  # noqa: E402

EVAL_TOPICS = [
    '/image_raw',
    '/lidar_raw',
    '/lidar_processed',
    '/lidar_obstacle_info',
    '/lidar_lane1_min',
    '/detections',
    '/yolov8_lane_info',
    '/yolov8_traffic_light_info',
    '/lane_control_info',
    '/roi_image',
    '/path_planning_result',
    '/topic_control_signal',
    '/finish_stop_reason',
    '/tf',
]

VIS_TOPICS = [
    '/yolov8_visualized_img',
    '/path_visualized_img',
]


def _truthy(text: str) -> bool:
    return text.strip().lower() in ('1', 'true', 'yes', 'on')


def _ros_node(**kwargs):
    kwargs.setdefault('output', 'screen')
    kwargs.setdefault('sigterm_timeout', '2.0')
    kwargs.setdefault('sigkill_timeout', '1.0')
    return Node(**kwargs)


def _start_bag(context, *args, **kwargs):
    if not _truthy(LaunchConfiguration('record').perform(context)):
        return [LogInfo(msg='[main] bag record disabled (record:=false)')]

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    bag_dir = LaunchConfiguration('bag_dir').perform(context).strip()
    if not bag_dir:
        bag_dir = str(workspace_root() / 'bags')
    Path(bag_dir).mkdir(parents=True, exist_ok=True)
    bag_path = str(Path(bag_dir) / f'main_{stamp}')

    topics = list(EVAL_TOPICS)
    if not _truthy(LaunchConfiguration('skip_visualized').perform(context)):
        topics.extend(VIS_TOPICS)

    Path(bag_path).mkdir(parents=True, exist_ok=False)
    (Path(bag_path) / 'topics.txt').write_text('\n'.join(topics) + '\n')

    cmd = [
        'ros2', 'bag', 'record',
        '--include-unpublished-topics',
        '-o', str(Path(bag_path) / 'eval'),
        *topics,
    ]
    return [
        LogInfo(msg=f'[main] recording -> {bag_path}/eval'),
        LogInfo(msg='[main] topics: ' + ' '.join(topics)),
        ExecuteProcess(
            cmd=cmd,
            output='screen',
            name='main_bag_record',
            sigterm_timeout='3.0',
            sigkill_timeout='2.0',
        ),
    ]


def generate_launch_description():
    model = LaunchConfiguration('model')
    use_lane_surface_control = LaunchConfiguration('use_lane_surface_control')
    drive_speed = LaunchConfiguration('drive_speed')
    steer_max = LaunchConfiguration('steer_max')
    steer_k = LaunchConfiguration('steer_k')
    steer_alpha = LaunchConfiguration('steer_alpha')
    steer_rate = LaunchConfiguration('steer_rate')
    control_cutting_idx = LaunchConfiguration('control_cutting_idx')
    control_min_area = LaunchConfiguration('control_min_area')

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
        DeclareLaunchArgument(
            'use_lane_surface_control',
            default_value='true',
            description='true: teamop lane2 BEV surface P+EMA+slew, false: legacy bang-bang',
        ),
        DeclareLaunchArgument(
            'drive_speed',
            default_value='250',
            description='Left/right wheel PWM while lane following',
        ),
        DeclareLaunchArgument(
            'steer_max',
            default_value='7',
            description='Maximum steering command magnitude',
        ),
        DeclareLaunchArgument(
            'steer_k',
            default_value='0.028',
            description='BEV lane-center P gain [steering step/pixel]',
        ),
        DeclareLaunchArgument(
            'steer_alpha',
            default_value='1.0',
            description='Steering EMA alpha (1 disables EMA)',
        ),
        DeclareLaunchArgument(
            'steer_rate',
            default_value='7.0',
            description='Maximum steering change per 0.1 s tick (7 disables slew)',
        ),
        DeclareLaunchArgument(
            'control_cutting_idx',
            default_value='0',
            description='Rows removed from top of filled lane2 BEV for control',
        ),
        DeclareLaunchArgument(
            'control_min_area',
            default_value='1000.0',
            description='Minimum filled BEV lane area for valid control',
        ),
        DeclareLaunchArgument(
            'record',
            default_value='true',
            description='Record eval bag while driving (Ctrl+C closes bag)',
        ),
        DeclareLaunchArgument(
            'bag_dir',
            default_value='',
            description='Bag parent directory (default: <ros2_ws>/bags)',
        ),
        DeclareLaunchArgument(
            'skip_visualized',
            default_value='false',
            description='Omit overlay image topics to reduce bag size',
        ),
        _ros_node(
            package='camera_perception_pkg',
            executable='image_publisher_node',
            name='image_publisher_node',
            output='screen'
        ),
        _ros_node(
            package='camera_perception_pkg',
            executable='yolov8_node',
            name='yolov8_node',
            output='screen',
            parameters=[{'model': model}],
        ),
        _ros_node(
            package='camera_perception_pkg',
            executable='lane_info_extractor_node',
            name='lane_info_extractor_node',
            output='screen',
            parameters=[{
                'control_cutting_idx': ParameterValue(
                    control_cutting_idx, value_type=int
                ),
                'control_min_area': ParameterValue(
                    control_min_area, value_type=float
                ),
            }],
        ),
        _ros_node(
            package='camera_perception_pkg',
            executable='traffic_light_detector_node',
            name='traffic_light_detector_node',
            output='screen',
        ),
        _ros_node(
            package='lidar_perception_pkg',
            executable='lidar_publisher_node',
            name='lidar_publisher_node',
            output='screen',
        ),
        _ros_node(
            package='lidar_perception_pkg',
            executable='lidar_processor_node',
            name='lidar_processor_node',
            output='screen',
        ),
        _ros_node(
            package='lidar_perception_pkg',
            executable='lidar_obstacle_detector_node',
            name='lidar_obstacle_detector_node',
            output='screen',
        ),
        _ros_node(
            package='decision_making_pkg',
            executable='motion_planner_node',
            name='motion_planner_node',
            output='screen',
            parameters=[{
                'require_green_start': ParameterValue(
                    LaunchConfiguration('require_green_start'), value_type=bool
                ),
                'use_lane_surface_control': ParameterValue(
                    use_lane_surface_control, value_type=bool
                ),
                'drive_speed': ParameterValue(drive_speed, value_type=int),
                'steer_max': ParameterValue(steer_max, value_type=int),
                'steer_k': ParameterValue(steer_k, value_type=float),
                'steer_alpha': ParameterValue(steer_alpha, value_type=float),
                'steer_rate': ParameterValue(steer_rate, value_type=float),
            }],
        ),
        _ros_node(
            package='decision_making_pkg',
            executable='path_planner_node',
            name='path_planner_node',
            output='screen'
        ),
        _ros_node(
            package='serial_communication_pkg',
            executable='serial_sender_node',
            name='serial_sender_node',
            output='screen',
        ),
        _ros_node(
            package='debug_pkg',
            executable='yolov8_visualizer_node',
            name='yolov8_visualizer_node',
            output='screen',
            condition=IfCondition(LaunchConfiguration('debug')),
        ),
        _ros_node(
            package='debug_pkg',
            executable='path_visualizer_node',
            name='path_visualizer_node',
            output='screen',
            condition=IfCondition(LaunchConfiguration('debug')),
        ),
        OpaqueFunction(function=_start_bag),
        RegisterEventHandler(
            OnShutdown(
                on_shutdown=[
                    ExecuteProcess(
                        cmd=[
                            'bash',
                            str(workspace_root() / 'scripts' / 'stop_main_nodes.sh'),
                        ],
                        output='screen',
                        name='stop_main_nodes',
                    )
                ]
            )
        ),
    ])
