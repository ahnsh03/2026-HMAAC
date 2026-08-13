import os

from . import camera_perception_func_lib


def get_path(file_name=None):
    """이 패키지 lib 디렉터리 기준 경로. 워크스페이스 위치와 무관하다."""
    lib_dir = os.path.dirname(os.path.realpath(__file__))
    if not file_name:
        return lib_dir
    return os.path.join(lib_dir, file_name)
