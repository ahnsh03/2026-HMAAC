import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSReliabilityPolicy

from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from interfaces_pkg.msg import DetectionArray
from .lib import camera_perception_func_lib as CPFL
from .lib.imgmsg import numpy_to_imgmsg
from .node_shutdown import close_cv_windows, install_shutdown

#---------------Variable Setting---------------
SUB_TOPIC_NAME = "detections"
LANE_CONTROL_TOPIC_NAME = "lane_control_info"
LANE_BEV_TOPIC_NAME = "lane2_control_bev"
SHOW_IMAGE = False
#----------------------------------------------


class Yolov8InfoExtractor(Node):
    def __init__(self):
        super().__init__('lane_info_extractor_node')

        self.sub_topic = self.declare_parameter('sub_detection_topic', SUB_TOPIC_NAME).value
        self.show_image = self.declare_parameter('show_image', SHOW_IMAGE).value
        if isinstance(self.show_image, str):
            self.show_image = self.show_image.strip().lower() in ("1", "true", "yes", "on")
        # 교육 기본 IPM. bev_calibrator(카메라 이미지)로 측정한 값만 launch로 덮어쓴다.
        self.src0_x = int(self.declare_parameter('src0_x', 238).value)
        self.src0_y = int(self.declare_parameter('src0_y', 316).value)
        self.src1_x = int(self.declare_parameter('src1_x', 402).value)
        self.src1_y = int(self.declare_parameter('src1_y', 313).value)
        self.src2_x = int(self.declare_parameter('src2_x', 501).value)
        self.src2_y = int(self.declare_parameter('src2_y', 476).value)
        self.src3_x = int(self.declare_parameter('src3_x', 155).value)
        self.src3_y = int(self.declare_parameter('src3_y', 476).value)
        # perception_debug / bev_calibrator가 넘기는 예전 ROI 인자. P 제어는 쓰지 않는다.
        self.declare_parameter('cutting_idx', 300)
        # 매 콜백 get_parameter. launch:= 와 ros2 param set 모두 바로 먹는다.
        # bag 스윕 승자: cut=160, p=2, β=1. center_mode:=moments near_blend:=0 이면 예전 모멘트만.
        self.declare_parameter('control_cutting_idx', 160)
        self.declare_parameter('control_min_area', 1000.0)
        self.declare_parameter('center_mode', 'moments')
        self.declare_parameter('row_mid_power', 2.0)
        self.declare_parameter('near_blend', 1.0)

        self.qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1
        )

        self.subscriber = self.create_subscription(
            DetectionArray, self.sub_topic, self.yolov8_detections_callback, self.qos_profile
        )
        self.lane_control_publisher = self.create_publisher(
            Float32MultiArray, LANE_CONTROL_TOPIC_NAME, self.qos_profile
        )
        self.lane_bev_publisher = self.create_publisher(
            Image, LANE_BEV_TOPIC_NAME, self.qos_profile
        )

        if self.show_image:
            try:
                cv2.namedWindow('lane2_control_bev', cv2.WINDOW_NORMAL)
                cv2.waitKey(1)
            except Exception as exc:
                self.get_logger().warn(f"namedWindow failed: {exc}")
                self.show_image = False

    def yolov8_detections_callback(self, detection_msg: DetectionArray):
        if len(detection_msg.detections) == 0:
            self._publish_lane_control(None, 0.0)
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank, "no detections (waiting YOLO)", (30, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            self._publish_bev_image(blank)
            return

        lane2_filled_image = CPFL.draw_filled_masks(
            detection_msg, cls_name='lane2', color=255
        )

        (h, w) = (lane2_filled_image.shape[0], lane2_filled_image.shape[1])
        dst_mat = [[round(w * 0.3), round(h * 0.0)], [round(w * 0.7), round(h * 0.0)], [round(w * 0.7), h], [round(w * 0.3), h]]
        src_mat = [
            [self.src0_x, self.src0_y],
            [self.src1_x, self.src1_y],
            [self.src2_x, self.src2_y],
            [self.src3_x, self.src3_y],
        ]

        lane2_filled_bev = CPFL.bird_convert(
            lane2_filled_image, srcmat=src_mat, dstmat=dst_mat
        )
        control_cutting_idx = max(
            0, int(self.get_parameter('control_cutting_idx').value)
        )
        control_min_area = float(self.get_parameter('control_min_area').value)
        center_mode = str(self.get_parameter('center_mode').value).strip().lower()
        row_mid_power = float(self.get_parameter('row_mid_power').value)
        near_blend = float(self.get_parameter('near_blend').value)
        control_bev = CPFL.roi_rectangle_below(
            lane2_filled_bev, cutting_idx=control_cutting_idx
        )
        far_x, mask_area = CPFL.largest_component_center(
            control_bev, min_area=control_min_area
        )
        need_near = center_mode == 'row_mid' or near_blend > 0.0
        near_x = None
        if need_near:
            near_x, near_area = CPFL.row_midpoint_center(
                control_bev,
                power=row_mid_power,
                min_area=control_min_area,
            )
            if mask_area <= 0.0:
                mask_area = near_area
        if center_mode == 'row_mid':
            lane_center_x = near_x if near_x is not None else far_x
        else:
            lane_center_x = CPFL.blend_lane_center(far_x, near_x, near_blend)
        self._publish_lane_control(lane_center_x, mask_area)

        control_debug = cv2.cvtColor(
            cv2.convertScaleAbs(control_bev), cv2.COLOR_GRAY2BGR
        )
        cv2.line(
            control_debug,
            (w // 2, 0),
            (w // 2, max(0, control_debug.shape[0] - 1)),
            (255, 0, 0),
            2,
        )
        if (
            lane_center_x is not None
            and np.isfinite(lane_center_x)
            and control_debug.shape[0] > 0
        ):
            cv2.circle(
                control_debug,
                (round(lane_center_x), control_debug.shape[0] // 2),
                10,
                (0, 255, 255),
                -1,
            )
        self._publish_bev_image(control_debug)

    def _publish_lane_control(self, center_x, mask_area):
        msg = Float32MultiArray()
        msg.data = [
            float('nan') if center_x is None else float(center_x),
            float(mask_area),
        ]
        self.lane_control_publisher.publish(msg)

    def _publish_bev_image(self, image):
        self.lane_bev_publisher.publish(numpy_to_imgmsg(image, encoding='bgr8'))
        if self.show_image:
            cv2.imshow('lane2_control_bev', image)
            cv2.waitKey(1)


def main(args=None):
    install_shutdown(close_cv=True)
    rclpy.init(args=args)
    node = Yolov8InfoExtractor()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        print("\n\nshutdown\n\n")
    finally:
        close_cv_windows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
