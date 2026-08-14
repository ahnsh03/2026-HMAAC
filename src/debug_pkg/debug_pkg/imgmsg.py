"""OpenCV 배열 ↔ sensor_msgs/Image. pip OpenCV 5 + Humble cv_bridge 우회."""
import numpy as np
from sensor_msgs.msg import Image


def imgmsg_to_numpy(msg: Image) -> np.ndarray:
    nchan = 4 if msg.encoding in ('bgra8', 'rgba8') else (
        1 if msg.encoding in ('mono8', '8UC1') else 3
    )
    image = np.frombuffer(msg.data, dtype=np.uint8)
    image = image.reshape((int(msg.height), int(msg.width), nchan))
    if msg.encoding in ('rgb8', 'rgba8'):
        image = image[:, :, :3][:, :, ::-1]
    elif nchan == 1:
        image = np.repeat(image, 3, axis=2)
    elif nchan == 4:
        image = image[:, :, :3]
    return np.ascontiguousarray(image)


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
