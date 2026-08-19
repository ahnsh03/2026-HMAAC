import rclpy 
from rclpy.node import Node 
from sensor_msgs.msg import Image 
from std_msgs.msg import Header

from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSReliabilityPolicy

import sys
import cv2
import os
import numpy as np

from .lib.imgmsg import numpy_to_imgmsg
from .node_shutdown import close_cv_windows, install_shutdown

#---------------Variable Setting---------------
# Publish할 토픽 이름
PUB_TOPIC_NAME = 'image_raw'

# 데이터 입력 소스: 'camera', 'image', 또는 'video' 중 택1하여 입력
DATA_SOURCE = 'camera' # camera: 카메라(웹캠)에서 이미지 입력, image: 이미지 데이터가 들어있는 디렉토리에서 이미지 입력, video: 비디오 데이터 파일에서 이미지 입력
# video -> camera
# 카메라(웹캠) 장치 번호 (ls /dev/video* 명령을 터미널 창에 입력하여 확인)
CAM_NUM = 2 # /dev/video2

# 이미지/비디오 경로는 cwd가 아니라 이 패키지 위치 기준
_DATASETS_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'lib',
    'Collected_Datasets',
)
IMAGE_DIRECTORY_PATH = os.path.join(_DATASETS_DIR, 'sample_dataset')
VIDEO_FILE_PATH = os.path.join(_DATASETS_DIR, 'driving_simulation.mp4')

# 화면에 publish하는 이미지를 띄울것인지 여부: True, 또는 False 중 택1하여 입력
SHOW_IMAGE = True

# 이미지 발행 주기 (초) - 소수점 필요 (int형은 반영되지 않음)
TIMER = 0.03
#----------------------------------------------

class ImagePublisherNode(Node):
    def __init__(self, data_source=DATA_SOURCE, cam_num=CAM_NUM, img_dir=IMAGE_DIRECTORY_PATH, video_path=VIDEO_FILE_PATH, pub_topic=PUB_TOPIC_NAME, logger=SHOW_IMAGE, timer=TIMER):
        super().__init__('image_publisher_node')
        self.declare_parameter('data_source', data_source)
        self.declare_parameter('cam_num', cam_num)
        self.declare_parameter('img_dir', img_dir)
        self.declare_parameter('video_path', video_path)
        self.declare_parameter('pub_topic', pub_topic)
        self.declare_parameter('logger', logger)
        self.declare_parameter('timer', timer)
        
        self.data_source = self.get_parameter('data_source').get_parameter_value().string_value
        self.cam_num = self.get_parameter('cam_num').get_parameter_value().integer_value
        self.img_dir = self.get_parameter('img_dir').get_parameter_value().string_value
        self.video_path = self.get_parameter('video_path').get_parameter_value().string_value
        self.pub_topic = self.get_parameter('pub_topic').get_parameter_value().string_value
        self.logger = self.get_parameter('logger').get_parameter_value().bool_value
        self.timer_period = self.get_parameter('timer').get_parameter_value().double_value

        self.qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1
        )
        
        self._read_fail_count = 0

        if self.data_source == 'camera':
            self.cap = cv2.VideoCapture(self.cam_num, cv2.CAP_V4L2)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if not self.cap.isOpened():
                self.get_logger().error(
                    f'Cannot open /dev/video{self.cam_num}. '
                    'Check ls /dev/video* and pass cam_num:=N')
                rclpy.shutdown()
                sys.exit(1)
            ok, test = self.cap.read()
            if not ok or test is None:
                self.get_logger().error(
                    f'/dev/video{self.cam_num} opened but first read failed')
                rclpy.shutdown()
                sys.exit(1)
            self.get_logger().info(
                f'Camera /dev/video{self.cam_num} OK shape={tuple(test.shape)}')
        elif self.data_source == 'video':
            self.cap = cv2.VideoCapture(self.video_path)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if not self.cap.isOpened():
                self.get_logger().error('Cannot open video file: %s' % self.video_path)
                rclpy.shutdown()
                sys.exit(1)
        elif self.data_source == 'image':
            if os.path.isdir(self.img_dir):
                self.img_list = sorted(os.listdir(self.img_dir))
                self.img_num = 0
            else:
                self.get_logger().error('Not a directory file: %s' % self.img_dir)
                rclpy.shutdown()
                sys.exit(1)
        else:
            self.get_logger().error("Wrong data source: %s \nCheck that the DATA_SOURCE variable is either 'camera', 'image', or 'video'." % self.data_source)
            rclpy.shutdown()
            sys.exit(1)
        self.publisher = self.create_publisher(Image, self.pub_topic, self.qos_profile)
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

    def _as_bgr8(self, frame):
        frame = np.ascontiguousarray(frame)
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return np.ascontiguousarray(frame, dtype=np.uint8)

    def _publish_frame(self, frame):
        # cv_bridge+OpenCV5 KeyError: 16 회피
        image_msg = numpy_to_imgmsg(self._as_bgr8(frame), encoding='bgr8')
        image_msg.header = Header()
        image_msg.header.stamp = self.get_clock().now().to_msg()
        image_msg.header.frame_id = 'image_frame'
        self.publisher.publish(image_msg)
        return frame

    def timer_callback(self):
        if self.data_source == 'camera':
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self._read_fail_count += 1
                if self._read_fail_count in (1, 30, 150):
                    self.get_logger().warn(
                        f'camera read failed x{self._read_fail_count} '
                        f'(/dev/video{self.cam_num})')
                return
            self._read_fail_count = 0
            try:
                frame = cv2.resize(frame, (640, 480))
                self._publish_frame(frame)
                if self.logger:
                    cv2.imshow('Camera Image', frame)
                    cv2.waitKey(1)
            except Exception as exc:
                self.get_logger().error(f'camera publish failed: {exc}')
                return
        elif self.data_source == 'image':
            while self.img_num < len(self.img_list):
                img_file = self.img_list[self.img_num]
                img_path = os.path.join(self.img_dir, img_file)
                img = cv2.imread(img_path)
                if img is None:
                    self.get_logger().warn('Skipping non-image file: %s' % img_file)
                else:
                    img = cv2.resize(img, (640, 480))
                    self._publish_frame(img)
                    if self.logger:
                        self.get_logger().info('Published image: %s' % img_file)
                        cv2.imshow('Saved Image', img)
                        cv2.waitKey(1)

                self.img_num += 1
                break
            else:
                self.img_num = 0
        elif self.data_source == 'video':
            ret, img = self.cap.read()
            if ret:
                img = cv2.resize(img, (640, 480))
                self._publish_frame(img)
                if self.logger:
                    cv2.imshow('Video Frame', img)
                    cv2.waitKey(1)
            else:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset video to the first frame
    
def main(args=None):
    install_shutdown(close_cv=True)
    rclpy.init(args=args)
    node = ImagePublisherNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        print("\n\nshutdown\n\n")
    finally:
        if getattr(node, 'cap', None) is not None and node.cap.isOpened():
            node.cap.release()
        close_cv_windows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
  
if __name__ == '__main__':
    main()
