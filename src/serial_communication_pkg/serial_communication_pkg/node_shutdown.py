"""SIGINT/SIGTERM/SIGHUP에서 프로세스를 종료한다."""
import signal


def install_shutdown():
    def _handle(signum, frame):
        raise SystemExit(0)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        try:
            signal.signal(sig, _handle)
        except (ValueError, OSError):
            pass
