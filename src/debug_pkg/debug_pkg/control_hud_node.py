"""카메라 위에 조향/속도/타겟점을 그린 HUD."""

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import String

from interfaces_pkg.msg import LaneInfo, MotionCommand


class ControlHudNode(Node):
    def __init__(self):
        super().__init__("control_hud_node")
        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1,
        )
        self.bridge = CvBridge()
        self.frame = None
        self.cmd = None
        self.lane = None
        self.debug = ""
        self.show = bool(self.declare_parameter("show_image", True).value)
        self.create_subscription(Image, "image_raw", self._on_img, qos)
        self.create_subscription(MotionCommand, "topic_control_signal", self._on_cmd, qos)
        self.create_subscription(LaneInfo, "yolov8_lane_info", self._on_lane, qos)
        self.create_subscription(String, "control_debug", self._on_dbg, qos)
        self.pub = self.create_publisher(Image, "control_hud_img", qos)

    def _on_img(self, msg: Image):
        self.frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        self._draw(msg)

    def _on_cmd(self, msg: MotionCommand):
        self.cmd = msg

    def _on_lane(self, msg: LaneInfo):
        self.lane = msg

    def _on_dbg(self, msg: String):
        self.debug = msg.data

    def _draw(self, img_msg: Image):
        if self.frame is None:
            return
        vis = self.frame.copy()
        y = 28
        lines = []
        if self.cmd is not None:
            lines.append(
                f"steer={self.cmd.steering}  L={self.cmd.left_speed}  R={self.cmd.right_speed}"
            )
        else:
            lines.append("steer=n/a (motion not running?)")
        if self.lane is not None:
            lines.append(f"slope={self.lane.slope:.2f}  pts={len(self.lane.target_points)}")
        if self.debug:
            lines.append(self.debug[:80])
        for text in lines:
            cv2.putText(
                vis,
                text,
                (12, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            y += 26
        out = self.bridge.cv2_to_imgmsg(vis, encoding="bgr8")
        out.header = img_msg.header
        self.pub.publish(out)
        if self.show:
            cv2.imshow("control_hud", vis)
            cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = ControlHudNode()
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
