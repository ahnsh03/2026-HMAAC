"""lane2 마스크 IPM/BEV 트랙바 캘리브레이션.

기본 src_mat 는 lane_info_extractor 하드코딩과 같다.
  p : launch 파라미터 문자열 출력
  s : src_mat.json 저장 (HMAAC_SESSION 또는 cwd)
  q : 종료
"""

import json
import os

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy

from camera_perception_pkg.lib import camera_perception_func_lib as CPFL
from interfaces_pkg.msg import DetectionArray

DEFAULT_SRC = [(238, 316), (402, 313), (501, 476), (155, 476)]
WIN = "bev_calibrator"


def _tb(name, value, maxv):
    cv2.createTrackbar(name, WIN, int(value), int(maxv), lambda _x: None)


def _get(name):
    return cv2.getTrackbarPos(name, WIN)


class BevCalibratorNode(Node):
    def __init__(self):
        super().__init__("bev_calibrator_node")
        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1,
        )
        self.edge = None
        self.create_subscription(DetectionArray, "detections", self._on_det, qos)
        cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
        w, h = 640, 480
        for i, (x, y) in enumerate(DEFAULT_SRC):
            _tb(f"src{i}_x", x, w - 1)
            _tb(f"src{i}_y", y, h - 1)
        _tb("cutting_idx", 300, h - 1)
        self.get_logger().info("p=print params  s=save json  q=quit")

    def _on_det(self, msg: DetectionArray):
        if len(msg.detections) == 0:
            return
        try:
            self.edge = CPFL.draw_edges(msg, cls_name="lane2", color=255)
        except Exception as exc:
            self.get_logger().warn(f"draw_edges: {exc}")

    def current_src(self):
        pts = []
        for i in range(4):
            pts.append([_get(f"src{i}_x"), _get(f"src{i}_y")])
        return pts

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
        payload = {"src_mat": src, "cutting_idx": cut}
        session = os.environ.get("HMAAC_SESSION", "")
        path = os.path.join(session, "src_mat.json") if session else "src_mat.json"
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
        self.get_logger().info(f"saved {path}")

    def render(self):
        if self.edge is None:
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                blank,
                "waiting /detections lane2 ...",
                (20, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )
            cv2.imshow(WIN, blank)
            return
        edge = self.edge.copy()
        if edge.dtype != np.uint8:
            edge = cv2.convertScaleAbs(edge)
        h, w = edge.shape[:2]
        src = np.float32(self.current_src())
        dst = np.float32(
            [
                [round(w * 0.3), 0],
                [round(w * 0.7), 0],
                [round(w * 0.7), h],
                [round(w * 0.3), h],
            ]
        )
        vis_src = cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR)
        for i, (x, y) in enumerate(src.astype(int)):
            cv2.circle(vis_src, (int(x), int(y)), 6, (0, 0, 255), -1)
            cv2.putText(
                vis_src,
                str(i),
                (int(x) + 6, int(y) - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )
        cv2.polylines(vis_src, [src.astype(np.int32)], True, (0, 255, 255), 1)

        bev = CPFL.bird_convert(edge, srcmat=src.tolist(), dstmat=dst.tolist())
        bev_u8 = cv2.convertScaleAbs(bev)
        cut = _get("cutting_idx")
        cut = min(max(cut, 0), max(h - 1, 0))
        roi = bev_u8[cut:] if cut < bev_u8.shape[0] else bev_u8
        bev_bgr = cv2.cvtColor(bev_u8, cv2.COLOR_GRAY2BGR)
        cv2.line(bev_bgr, (0, cut), (w - 1, cut), (0, 0, 255), 1)
        roi_bgr = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR) if roi.size else bev_bgr
        roi_bgr = cv2.resize(roi_bgr, (w, h))
        mosaic = np.hstack([vis_src, bev_bgr, roi_bgr])
        cv2.imshow(WIN, mosaic)


def main(args=None):
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
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
