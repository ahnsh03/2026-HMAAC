"""OpenCV 배열 → sensor_msgs/Image. pip OpenCV 5 + Humble cv_bridge 우회."""
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
