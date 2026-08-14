import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import QoSReliabilityPolicy
from sensor_msgs.msg import Image

from .imgmsg import imgmsg_to_numpy, numpy_to_imgmsg
from .node_shutdown import close_cv_windows, install_shutdown

WINDOW_NAME = 'race_viz'
PANEL_W = 480
PANEL_H = 360


def _placeholder(label: str, width: int, height: int) -> np.ndarray:
    panel = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(
        panel, f'waiting {label}', (20, height // 2),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2,
    )
    return panel


def _panel(image, label: str, width: int, height: int) -> np.ndarray:
    if image is None:
        panel = _placeholder(label, width, height)
    else:
        panel = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    cv2.rectangle(panel, (0, 0), (width - 1, 28), (0, 0, 0), -1)
    cv2.putText(
        panel, label, (8, 21),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
    )
    return panel


class VizMosaicNode(Node):
    def __init__(self):
        super().__init__('viz_mosaic_node')
        self.show_image = self.declare_parameter('show_image', True).value
        if isinstance(self.show_image, str):
            self.show_image = self.show_image.strip().lower() in ('1', 'true', 'yes', 'on')
        self.panel_w = int(self.declare_parameter('panel_w', PANEL_W).value)
        self.panel_h = int(self.declare_parameter('panel_h', PANEL_H).value)

        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1,
        )
        self.camera = None
        self.yolo = None
        self.bev = None
        self.create_subscription(Image, 'image_raw', self._camera_cb, qos)
        self.create_subscription(Image, 'yolov8_visualized_img', self._yolo_cb, qos)
        self.create_subscription(Image, 'lane2_control_bev', self._bev_cb, qos)
        self.publisher = self.create_publisher(Image, 'race_viz', qos)
        self.create_timer(0.05, self._tick)

        if self.show_image:
            try:
                cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(WINDOW_NAME, self.panel_w * 2, self.panel_h * 2)
                cv2.waitKey(1)
            except Exception as exc:
                self.get_logger().warn(f'namedWindow failed: {exc}')
                self.show_image = False

    def _camera_cb(self, msg: Image):
        self.camera = imgmsg_to_numpy(msg)

    def _yolo_cb(self, msg: Image):
        self.yolo = imgmsg_to_numpy(msg)

    def _bev_cb(self, msg: Image):
        self.bev = imgmsg_to_numpy(msg)

    def _tick(self):
        top = np.hstack((
            _panel(self.camera, 'camera', self.panel_w, self.panel_h),
            _panel(self.yolo, 'yolo', self.panel_w, self.panel_h),
        ))
        bottom = _panel(self.bev, 'bev', self.panel_w * 2, self.panel_h)
        mosaic = np.vstack((top, bottom))
        self.publisher.publish(numpy_to_imgmsg(mosaic, encoding='bgr8'))
        if self.show_image:
            try:
                cv2.imshow(WINDOW_NAME, mosaic)
                cv2.waitKey(1)
            except Exception as exc:
                self.get_logger().warn(f'imshow failed: {exc}')
                self.show_image = False


def main(args=None):
    install_shutdown(close_cv=True)
    rclpy.init(args=args)
    node = VizMosaicNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        close_cv_windows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
