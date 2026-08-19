import serial
import marshal
import types
import os
import sys
import time
import select
import termios
import tty
from datetime import datetime

import cv2
import keyboard

real_path = os.path.dirname(os.path.realpath(__file__))
pyc = open((real_path) + '/data_collection_func_lib.cpython-310.pyc', 'rb').read()
code = marshal.loads(pyc[16:])
module = types.ModuleType('module_name')
exec(code, module.__dict__)

# 기존 키: w/s(속도), a/d(조향), r(리셋), c(프레임 저장), f(종료)
# 영상 녹화 토글은 중복되지 않는 'v' 사용
RECORD_KEY = 'v'
RECORD_FPS = 20.0
PREVIEW_WINDOW = 'Data Collection Preview'
CONTROL_KEYS = set('wsadrcf')
KEY_HOLD_SEC = 0.18  # process() 폴링에 잡히도록 짧게 유지


def log(msg):
    print(msg, flush=True)


def draw_preview(frame, recording, control_values, frame_count=0, elapsed=0.0):
    """프리뷰용 오버레이(녹화 상태/제어값)를 그린다."""
    view = frame.copy()
    if recording:
        cv2.circle(view, (24, 24), 10, (0, 0, 255), -1)
        cv2.putText(
            view, f'REC {frame_count}  {elapsed:.1f}s',
            (42, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA
        )
    else:
        cv2.putText(
            view, f'IDLE  press {RECORD_KEY} to record',
            (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 2, cv2.LINE_AA
        )

    hud = (
        f"steer:{control_values['steering']}  "
        f"L:{control_values['left_speed']}  "
        f"R:{control_values['right_speed']}"
    )
    cv2.putText(
        view, hud, (16, view.shape[0] - 16),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 255, 50), 2, cv2.LINE_AA
    )
    return view


def start_recording(data_collector, record_dir):
    """YOLO 학습/수동 라벨링용 영상 녹화 시작."""
    os.makedirs(record_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

    width = int(data_collector.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    height = int(data_collector.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

    candidates = [
        ('mp4', 'mp4v'),
        ('avi', 'MJPG'),
    ]

    writer = None
    video_path = None
    used_codec = None
    for ext, fourcc_str in candidates:
        video_path = os.path.join(record_dir, f'recording_{timestamp}.{ext}')
        fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        writer = cv2.VideoWriter(video_path, fourcc, RECORD_FPS, (width, height))
        if writer.isOpened():
            used_codec = f'{fourcc_str}/{ext}'
            break
        writer.release()
        writer = None
        if os.path.exists(video_path) and os.path.getsize(video_path) == 0:
            os.remove(video_path)

    if writer is None:
        log('[REC] ERROR: VideoWriter open failed for mp4v/MJPG')
        return None, None, 0, None

    log('=' * 60)
    log('[REC] START recording')
    log(f'[REC]   path     : {video_path}')
    log(f'[REC]   codec    : {used_codec}')
    log(f'[REC]   size     : {width}x{height}')
    log(f'[REC]   fps      : {RECORD_FPS}')
    log(f'[REC]   press "{RECORD_KEY}" again to stop')
    log('=' * 60)
    return writer, video_path, 0, (width, height)


def stop_recording(writer, video_path, frame_count, elapsed_sec):
    """영상 녹화 종료 및 리소스 정리."""
    if writer is not None:
        writer.release()

    file_size = os.path.getsize(video_path) if video_path and os.path.exists(video_path) else 0
    avg_fps = (frame_count / elapsed_sec) if elapsed_sec > 0 else 0.0

    log('=' * 60)
    log('[REC] STOP recording')
    log(f'[REC]   path     : {video_path}')
    log(f'[REC]   frames   : {frame_count}')
    log(f'[REC]   duration : {elapsed_sec:.2f}s')
    log(f'[REC]   avg fps  : {avg_fps:.2f}')
    log(f'[REC]   filesize : {file_size} bytes')

    if frame_count <= 0 or file_size < 1024:
        log('[REC] ERROR: no frames were written (empty/unplayable file)')
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
            log(f'[REC] removed empty file: {video_path}')
    log('=' * 60)


def install_rootless_keyboard(key_until):
    """root 없이 동작하도록 keyboard.is_pressed를 로컬 키 상태로 교체."""

    def is_pressed(key):
        return time.time() < key_until.get(str(key).lower(), 0.0)

    keyboard.is_pressed = is_pressed
    log('[INFO] rootless keyboard bridge enabled (no sudo needed for WASD)')


def main():
    DATA_PATH = os.path.normpath(os.path.join(
        real_path,
        '..',
        'camera_perception_pkg',
        'camera_perception_pkg',
        'lib',
        'Collected_Datasets',
    ))
    CAMERA_NUM = 2
    SERIAL_PORT = '/dev/ttyACM0'
    MAX_STEERING = 7

    log(DATA_PATH)
    log(f'[INFO] Video record toggle key: "{RECORD_KEY}" (start/stop)')
    log('[INFO] Control keys: w/s speed, a/d steer, r reset, c capture, f exit')
    log('[INFO] Focus the preview window OR this terminal, then press keys')
    log('[INFO] Sent logs print only when control values change')

    key_until = {}
    install_rootless_keyboard(key_until)

    data_collector = module.Data_Collect(path=DATA_PATH, cam_num=CAMERA_NUM, max_steering=MAX_STEERING)
    ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
    time.sleep(1)
    cv2.namedWindow(PREVIEW_WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(PREVIEW_WINDOW, 960, 720)

    recording = False
    video_writer = None
    video_path = None
    record_frame_count = 0
    record_start_time = None
    record_frame_size = None
    last_rec_log_time = 0.0
    last_sent_message = None
    last_heartbeat_time = time.time()

    TOGGLE_DEBOUNCE_SEC = 0.6
    toggle_pending = False
    last_toggle_time = 0.0

    def request_toggle(source):
        nonlocal toggle_pending, last_toggle_time
        now = time.time()
        if now - last_toggle_time < TOGGLE_DEBOUNCE_SEC:
            log(f'[REC] toggle ignored (debounce) via {source}')
            return
        toggle_pending = True
        last_toggle_time = now
        log(f'[REC] toggle requested via {source}')

    def note_key(ch, source):
        """한 글자 키 입력을 제어/녹화 토글에 반영."""
        if not ch:
            return
        k = ch.lower()
        if k == RECORD_KEY:
            request_toggle(source)
            return
        if k in CONTROL_KEYS:
            key_until[k] = time.time() + KEY_HOLD_SEC

    stdin_fd = None
    old_termios = None
    if sys.stdin.isatty():
        try:
            stdin_fd = sys.stdin.fileno()
            old_termios = termios.tcgetattr(stdin_fd)
            tty.setcbreak(stdin_fd)
            log('[INFO] terminal key mode enabled')
        except Exception as e:
            log(f'[WARN] terminal key mode unavailable: {e}')
            stdin_fd = None
            old_termios = None

    try:
        while True:
            # 1) 터미널 키
            if stdin_fd is not None:
                try:
                    while select.select([sys.stdin], [], [], 0)[0]:
                        note_key(sys.stdin.read(1), 'stdin')
                except Exception:
                    pass

            # 2) 프리뷰 창 키 (창에 포커스일 때)
            # waitKey는 아래에서 프레임 표시 후 호출

            if toggle_pending:
                toggle_pending = False
                if not recording:
                    video_writer, video_path, record_frame_count, record_frame_size = start_recording(
                        data_collector, data_collector.data_collection_path
                    )
                    if video_writer is not None:
                        recording = True
                        record_start_time = time.time()
                        last_rec_log_time = record_start_time
                else:
                    elapsed = time.time() - record_start_time if record_start_time else 0.0
                    stop_recording(video_writer, video_path, record_frame_count, elapsed)
                    recording = False
                    video_writer = None
                    video_path = None
                    record_frame_count = 0
                    record_start_time = None
                    record_frame_size = None

            result = data_collector.process()
            if result['exit']:
                ser.write(b's0l0r0\n')
                break

            control_values = data_collector.get_control_values()
            ret, frame = data_collector.cap.read()
            now = time.time()
            elapsed = (now - record_start_time) if (recording and record_start_time) else 0.0

            if ret:
                if recording and video_writer is not None:
                    write_frame = frame
                    if record_frame_size is not None:
                        tw, th = record_frame_size
                        if frame.shape[1] != tw or frame.shape[0] != th:
                            write_frame = cv2.resize(frame, (tw, th))
                    video_writer.write(write_frame)
                    record_frame_count += 1
                    if now - last_rec_log_time >= 1.0:
                        log(
                            f'[REC] recording... frames={record_frame_count} '
                            f'elapsed={elapsed:.1f}s '
                            f'steer={control_values["steering"]} '
                            f'L={control_values["left_speed"]} R={control_values["right_speed"]} '
                            f'file={os.path.basename(video_path)}'
                        )
                        last_rec_log_time = now

                preview = draw_preview(
                    frame, recording, control_values, record_frame_count, elapsed
                )
                cv2.imshow(PREVIEW_WINDOW, preview)
            elif recording:
                log('[REC] WARNING: failed to read frame from camera')

            key_code = cv2.waitKey(1) & 0xFF
            if key_code != 255:
                note_key(chr(key_code), 'preview')

            message = (
                f's{control_values["steering"]}'
                f'l{control_values["left_speed"]}'
                f'r{control_values["right_speed"]}\n'
            )
            ser.write(message.encode())

            if message != last_sent_message:
                prefix = '[REC] ' if recording else ''
                log(f'{prefix}Sent: {message.strip()}')
                last_sent_message = message
                last_heartbeat_time = now
            elif (not recording) and (now - last_heartbeat_time >= 2.0):
                log(f'Idle: {message.strip()} (a/d steer, {RECORD_KEY} record)')
                last_heartbeat_time = now

            if not recording:
                time.sleep(0.02)

    except KeyboardInterrupt:
        ser.write(b's0l0r0\n')
        log('Program interrupted.')
    finally:
        if old_termios is not None and stdin_fd is not None:
            try:
                termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_termios)
            except Exception:
                pass
        if recording and video_writer is not None:
            elapsed = time.time() - record_start_time if record_start_time else 0.0
            stop_recording(video_writer, video_path, record_frame_count, elapsed)
        try:
            ser.write(b's0l0r0\n')
            ser.close()
        except Exception:
            pass
        data_collector.cleanup()
        log('Serial connection closed.')


if __name__ == '__main__':
    main()
