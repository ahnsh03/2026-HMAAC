"""SIGINT/SIGTERM/SIGHUP에서 OpenCV 창을 닫고 프로세스를 종료한다."""
import atexit
import signal

_closed = False


def close_cv_windows():
    global _closed
    if _closed:
        return
    _closed = True
    try:
        import cv2
        cv2.destroyAllWindows()
        for _ in range(8):
            cv2.waitKey(1)
    except Exception:
        pass


def install_shutdown(close_cv=False):
    if close_cv:
        atexit.register(close_cv_windows)

    def _handle(signum, frame):
        if close_cv:
            close_cv_windows()
        raise SystemExit(0)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        try:
            signal.signal(sig, _handle)
        except (ValueError, OSError):
            pass
