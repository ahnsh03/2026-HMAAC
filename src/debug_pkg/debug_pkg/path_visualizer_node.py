import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSDurabilityPolicy, QoSReliabilityPolicy
from sensor_msgs.msg import Image
from interfaces_pkg.msg import PathPlanningResult
import cv2
import numpy as np
from cv_bridge import CvBridge
from .imgmsg import numpy_to_imgmsg
from .node_shutdown import close_cv_windows, install_shutdown

#---------------Variable Setting---------------
SUB_ROI_IMAGE_TOPIC = "roi_image"        # ROI 이미지 토픽
SUB_SPLINE_PATH_TOPIC = "path_planning_result"  # 경로 계획 결과 토픽
PUB_TOPIC_NAME = "path_visualized_img"      # 시각화된 이미지 퍼블리시 토픽

#----------------------------------------------
class PathVisualizerNode(Node):
    def __init__(self):
        super().__init__('path_visualizer_node')

        # 파라미터 선언
        self.sub_roi_image_topic = self.declare_parameter('sub_roi_image_topic', SUB_ROI_IMAGE_TOPIC).value
        self.sub_spline_path_topic = self.declare_parameter('sub_spline_path_topic', SUB_SPLINE_PATH_TOPIC).value
        self.pub_topic = self.declare_parameter('pub_topic', PUB_TOPIC_NAME).value
        self.show_image = self.declare_parameter('show_image', True).value
        if isinstance(self.show_image, str):
            self.show_image = self.show_image.strip().lower() in ("1", "true", "yes", "on")

        # QoS 설정
        self.qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1
        )

        # CvBridge 초기화
        self.cv_bridge = CvBridge()

        # 구독자 설정 (이미지 및 경로 구독)
        self.roi_image_sub = self.create_subscription(
            Image, self.sub_roi_image_topic, self.roi_image_callback, self.qos_profile)
        
        self.spline_path_sub = self.create_subscription(
            PathPlanningResult, self.sub_spline_path_topic, self.spline_path_callback, self.qos_profile)

        # 퍼블리셔 설정 (시각화된 이미지 퍼블리시)
        self.publisher = self.create_publisher(Image, self.pub_topic, self.qos_profile)

        # 이미지와 경로 데이터를 저장하기 위한 변수
        self.roi_image = None
        self.spline_path = None

        if self.show_image:
            try:
                cv2.namedWindow('path_visualized_img', cv2.WINDOW_NORMAL)
                cv2.waitKey(1)
            except Exception as e:
                self.get_logger().warn(f"namedWindow failed: {e}")
                self.show_image = False

    def roi_image_callback(self, msg: Image):
        try:
            img = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            if img.ndim == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            self.roi_image = np.ascontiguousarray(img)
        except Exception as e:
            self.get_logger().error(f"Failed to convert ROI image: {str(e)}")

    def spline_path_callback(self, msg: PathPlanningResult):
        self.spline_path = list(zip(msg.x_points, msg.y_points))
        if self.roi_image is not None and self.spline_path is not None:
            self.visualize_path()

    def visualize_path(self):
        vis = self.roi_image.copy()
        h, w = vis.shape[:2]
        for (x, y) in self.spline_path:
            px, py = int(x), int(y)
            if 0 <= px < w and 0 <= py < h:
                cv2.circle(vis, (px, py), 5, (0, 0, 255), -1)

        try:
            output_msg = numpy_to_imgmsg(vis, encoding='bgr8')
            self.publisher.publish(output_msg)
        except Exception as e:
            self.get_logger().error(f"Failed to convert image for publishing: {e}")
            return

        if self.show_image:
            try:
                cv2.imshow('path_visualized_img', vis)
                cv2.waitKey(1)
            except Exception as e:
                self.get_logger().warn(f"imshow failed: {e}")


def main(args=None):
    install_shutdown(close_cv=True)
    rclpy.init(args=args)
    node = PathVisualizerNode()
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
