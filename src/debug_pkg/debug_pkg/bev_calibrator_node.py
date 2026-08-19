"""카메라 이미지로 IPM/BEV 사다리꼴을 맞춘다. YOLO 마스크를 쓰지 않는다.

src_mat 는 장착 기하(노면 사다리꼴)이므로 가중치와 무관하다.
차선이 BEV에서 세로로 서게 맞춘 뒤, 같은 숫자로 여러 .pt 를 A/B 한다.

점 순서 (교육 기본값과 동일):
  0 원거리-좌, 1 원거리-우, 2 근거리-우, 3 근거리-좌

키: p = launch 인자 출력,  s = src_mat.json 저장,  q = 종료
"""

import json
import os

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Image
from .node_shutdown import close_cv_windows, install_shutdown

DEFAULT_SRC = [(238, 316), (402, 313), (501, 476), (155, 476)]
CORNER_LABELS = ("0 far-L", "1 far-R", "2 near-R", "3 near-L")
WIN = "bev_calibrator"


def _tb(name, value, maxv):
    cv2.createTrackbar(name, WIN, int(value), int(maxv), lambda _x: None)


def _get(name):
    return cv2.getTrackbarPos(name, WIN)


def _warp(bgr, src, dst):
    src_f = np.float32(src)
    dst_f = np.float32(dst)
    matrix = cv2.getPerspectiveTransform(src_f, dst_f)
    h, w = bgr.shape[:2]
    return cv2.warpPerspective(bgr, matrix, (w, h))


class BevCalibratorNode(Node):
    def __init__(self):
        super().__init__("bev_calibrator_node")
        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1,
        )
        self.bridge = CvBridge()
        self.frame = None
        self.create_subscription(Image, "image_raw", self._on_image, qos)
        cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
        w, h = 640, 480
        for i, (x, y) in enumerate(DEFAULT_SRC):
            _tb(f"src{i}_x", x, w - 1)
            _tb(f"src{i}_y", y, h - 1)
        _tb("cutting_idx", 300, h - 1)
        self.get_logger().info(
            "Fit the trapezoid to the 2nd-lane road in the camera image. "
            "p=print  s=save json  q=quit"
        )

    def _on_image(self, msg: Image):
        try:
            self.frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().warn(f"cv_bridge: {exc}")

    def current_src(self):
        return [[_get(f"src{i}_x"), _get(f"src{i}_y")] for i in range(4)]

    def print_params(self):
        src = self.current_src()
        cut = _get("cutting_idx")
        args = " ".join(
            f"src{i}_{ax}:={src[i][j]}"
            for i in range(4)
            for j, ax in enumerate("xy")
        )
        line = f"{args} cutting_idx:={cut}"
        print(line)
        self.get_logger().info(line)
        return src, cut

    def save_json(self):
        src, cut = self.print_params()
        path = os.path.join(os.environ.get("HMAAC_SESSION", "") or ".", "src_mat.json")
        with open(path, "w") as f:
            json.dump({"src_mat": src, "cutting_idx": cut}, f, indent=2)
        self.get_logger().info(f"saved {path}")

    def render(self):
        if self.frame is None:
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                blank,
                "waiting /image_raw ...",
                (20, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )
            cv2.imshow(WIN, blank)
            return

        vis = self.frame.copy()
        h, w = vis.shape[:2]
        src = np.float32(self.current_src())
        dst = np.float32(
            [
                [round(w * 0.3), 0],
                [round(w * 0.7), 0],
                [round(w * 0.7), h],
                [round(w * 0.3), h],
            ]
        )
        for i, (x, y) in enumerate(src.astype(int)):
            cv2.circle(vis, (int(x), int(y)), 6, (0, 0, 255), -1)
            cv2.putText(
                vis,
                CORNER_LABELS[i],
                (int(x) + 6, int(y) - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )
        cv2.polylines(vis, [src.astype(np.int32)], True, (0, 255, 255), 2)

        bev = _warp(self.frame, src, dst)
        cut = min(max(_get("cutting_idx"), 0), max(h - 1, 0))
        cv2.line(bev, (0, cut), (w - 1, cut), (0, 0, 255), 1)
        roi = bev[cut:] if cut < bev.shape[0] else bev
        roi = cv2.resize(roi, (w, h)) if roi.size else bev
        hint = "trapezoid on road  |  lanes should be vertical in BEV"
        cv2.putText(vis, hint, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        mosaic = np.hstack([vis, bev, roi])
        cv2.imshow(WIN, mosaic)


def main(args=None):
    install_shutdown(close_cv=True)
    rclpy.init(args=args)
    node = BevCalibratorNode()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.03)
            node.render()
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("p"):
                node.print_params()
            if key == ord("s"):
                node.save_json()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        close_cv_windows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
