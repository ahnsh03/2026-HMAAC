"""이 런치 파일이 속한 ros2_ws 루트만 사용한다. reference 워크스페이스는 무시한다."""
import os
from pathlib import Path


def _is_team_workspace(path: Path) -> bool:
    path = path.resolve()
    if "reference" in path.parts:
        return False
    return (
        (path / "src" / "launch_pkg").is_dir()
        and (path / "src" / "camera_perception_pkg").is_dir()
    )


def workspace_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if _is_team_workspace(parent):
            try:
                here.relative_to(parent)
            except ValueError:
                continue
            return parent

    for prefix in os.environ.get("COLCON_PREFIX_PATH", "").split(os.pathsep):
        if not prefix:
            continue
        install_dir = Path(prefix).resolve()
        if not install_dir.is_dir() or install_dir.name != "install":
            continue
        candidate = install_dir.parent
        if _is_team_workspace(candidate):
            return candidate

    raise FileNotFoundError(
        "team ros2_ws root not found from " + str(here)
    )


def default_yolo_weights() -> str:
    root = workspace_root()
    candidates = [
        root / "best.pt",
        root / "weights" / "team14_best.pt",
        root / "weights" / "best.pt",
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return str(candidates[0])
