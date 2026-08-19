"""OpenCV 배열 → sensor_msgs/Image.

Humble cv_bridge는 OpenCV 4 타입코드(CV_8UC3=16)를 쓰는데,
pip OpenCV 5는 CV_8UC3=64라 cv2_to_imgmsg(..., encoding='bgr8')가
KeyError: 16 으로 노드를 죽인다. 여기선 타입표를 거치지 않는다.
"""
import numpy as np
from sensor_msgs.msg import Image


def numpy_to_imgmsg(cvim, encoding='bgr8', header=None) -> Image:
    cvim = np.ascontiguousarray(cvim)
    msg = Image()
    if header is not None:
        msg.header = header
    msg.height = int(cvim.shape[0])
    msg.width = int(cvim.shape[1])
    nchan = 1 if cvim.ndim == 2 else int(cvim.shape[2])
    if encoding in ('passthrough', '', None):
        encoding = 'mono8' if nchan == 1 else ('bgra8' if nchan == 4 else 'bgr8')
    msg.encoding = encoding
    msg.is_bigendian = 0
    msg.step = int(msg.width * nchan * cvim.dtype.itemsize)
    msg.data = cvim.tobytes()
    return msg
