"""수동 마커: START / LAP1 / LAP2 / STOP_TRY.

창이 포커스일 때:
  s START · 1 LAP1 · 2 LAP2 · t STOP_TRY · q 종료

또는:
  ros2 topic pub --once /debug_marker_cmd std_msgs/String "data: START"

HMAAC_SESSION 이 있으면 markers.csv 에 남긴다.
"""

import csv
import os
from datetime import datetime

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

KEYS = {
    ord("s"): "START",
    ord("S"): "START",
    ord("1"): "LAP1",
    ord("2"): "LAP2",
    ord("t"): "STOP_TRY",
    ord("T"): "STOP_TRY",
}


class MarkerNode(Node):
    def __init__(self):
        super().__init__("marker_node")
        self.session = os.environ.get("HMAAC_SESSION", "")
        self.csv_path = os.path.join(self.session, "markers.csv") if self.session else ""
        self.pub = self.create_publisher(String, "debug_markers", 10)
        self.create_subscription(String, "debug_marker_cmd", self._on_cmd, 10)
        if self.csv_path and not os.path.exists(self.csv_path):
            os.makedirs(self.session, exist_ok=True)
            with open(self.csv_path, "w", newline="") as f:
                csv.writer(f).writerow(["iso_time", "stamp_ns", "label"])
        self.get_logger().info(
            f"keys: s=START 1=LAP1 2=LAP2 t=STOP_TRY  session={self.session or '(none)'}"
        )

    def _on_cmd(self, msg: String):
        label = msg.data.strip().upper()
        if label:
            self.emit(label)

    def emit(self, label: str):
        now = self.get_clock().now()
        out = String()
        out.data = label
        self.pub.publish(out)
        iso = datetime.now().isoformat(timespec="seconds")
        self.get_logger().info(f"MARKER {label}")
        if self.csv_path:
            with open(self.csv_path, "a", newline="") as f:
                csv.writer(f).writerow([iso, now.nanoseconds, label])


def main(args=None):
    rclpy.init(args=args)
    node = MarkerNode()
    canvas = np.zeros((160, 480, 3), dtype=np.uint8)
    cv2.putText(
        canvas,
        "s START  1 LAP1  2 LAP2  t STOP  q quit",
        (12, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1,
        cv2.LINE_AA,
    )
    cv2.imshow("markers", canvas)
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.05)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key in KEYS:
                node.emit(KEYS[key])
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
