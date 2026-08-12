"""LaserScan top-down 시각화 (보넷 장착 정렬).

전방이 그림 위쪽. 빨간 부채꼴 = 장애물 게이트 기본값(0–30deg, 0.5–2.0m).
"""

import math

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Image, LaserScan
from cv_bridge import CvBridge


class LidarScanVisualizerNode(Node):
    def __init__(self):
        super().__init__("lidar_scan_visualizer_node")
        self.topic = self.declare_parameter("scan_topic", "lidar_raw").value
        self.show = bool(self.declare_parameter("show_image", True).value)
        self.px_per_m = float(self.declare_parameter("px_per_m", 80.0).value)
        self.max_range = float(self.declare_parameter("max_range", 4.0).value)
        self.gate_start = int(self.declare_parameter("gate_start_deg", 0).value)
        self.gate_end = int(self.declare_parameter("gate_end_deg", 30).value)
        self.gate_min = float(self.declare_parameter("gate_min_m", 0.5).value)
        self.gate_max = float(self.declare_parameter("gate_max_m", 2.0).value)

        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1,
        )
        self.bridge = CvBridge()
        self.create_subscription(LaserScan, self.topic, self._on_scan, qos)
        self.pub = self.create_publisher(Image, "lidar_visualized_img", qos)
        self.get_logger().info(f"scan={self.topic}  gate={self.gate_start}-{self.gate_end}deg")

    def _on_scan(self, msg: LaserScan):
        size = int(self.max_range * self.px_per_m * 2) + 40
        img = np.zeros((size, size, 3), dtype=np.uint8)
        cx = cy = size // 2
        scale = self.px_per_m

        def polar_to_px(angle_rad, rng):
            # 전방(+x 센서)을 이미지 위(+y 화면 반대)로: x_fwd = r cos, y_left = r sin
            x = rng * math.cos(angle_rad)
            y = rng * math.sin(angle_rad)
            px = int(cx - y * scale)
            py = int(cy - x * scale)
            return px, py

        # range rings
        for r_m in (1.0, 2.0, 3.0, self.max_range):
            rad = int(r_m * scale)
            cv2.circle(img, (cx, cy), rad, (40, 40, 40), 1)
            cv2.putText(
                img,
                f"{r_m:.0f}m",
                (cx + 4, cy - rad - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (80, 80, 80),
                1,
            )

        # gate wedge
        for deg in range(self.gate_start, self.gate_end + 1):
            a = math.radians(deg)
            p1 = polar_to_px(a, self.gate_min)
            p2 = polar_to_px(a, self.gate_max)
            cv2.line(img, p1, p2, (0, 0, 80), 1)

        angle = msg.angle_min
        for rng in msg.ranges:
            if math.isfinite(rng) and 0.05 < rng < self.max_range:
                px, py = polar_to_px(angle, rng)
                if 0 <= px < size and 0 <= py < size:
                    img[py, px] = (0, 255, 0)
            angle += msg.angle_increment

        cv2.circle(img, (cx, cy), 4, (0, 0, 255), -1)
        cv2.putText(
            img,
            "up=forward  red=obstacle gate",
            (8, 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
        )
        out = self.bridge.cv2_to_imgmsg(img, encoding="bgr8")
        out.header = msg.header
        self.pub.publish(out)
        if self.show:
            cv2.imshow("lidar_scan", img)
            cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = LidarScanVisualizerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
