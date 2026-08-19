import os
import types
import marshal


def get_path(file_name=None):
    """이 패키지 lib 디렉터리 기준 경로. 워크스페이스 위치와 무관하다."""
    lib_dir = os.path.dirname(os.path.realpath(__file__))
    if not file_name:
        return lib_dir
    return os.path.join(lib_dir, file_name)


def get_pyc(module_file):
    candidates = []
    seen = set()
    for base in (
        os.path.dirname(os.path.realpath(__file__)),
        os.path.dirname(os.path.abspath(__file__)),
    ):
        path = os.path.join(base, module_file)
        if path in seen:
            continue
        seen.add(path)
        candidates.append(path)
        if os.path.isfile(path):
            pyc = open(path, 'rb').read()
            code = marshal.loads(pyc[16:])
            module = types.ModuleType('module_name')
            exec(code, module.__dict__)
            return module
    raise FileNotFoundError('pyc not found, tried: ' + ', '.join(candidates))


lidar_perception_func_lib = get_pyc("lidar_perception_func_lib.cpython-310.pyc")
