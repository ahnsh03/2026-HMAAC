import serial
import marshal
import types
import os
import time
from datetime import datetime

import cv2
import keyboard

real_path = os.path.dirname(os.path.realpath(__file__))
pyc = open((real_path)+'/data_collection_func_lib.cpython-310.pyc', 'rb').read()
code = marshal.loads(pyc[16:])
module = types.ModuleType('module_name')
exec(code, module.__dict__)

# 기존 키: w/s(속도), a/d(조향), r(리셋), c(프레임 저장), f(종료)
# 영상 녹화 토글은 중복되지 않는 'v' 사용
RECORD_KEY = 'v'
RECORD_FPS = 20.0


def start_recording(data_collector, record_dir):
    """YOLO 학습/수동 라벨링용 영상 녹화 시작."""
    os.makedirs(record_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    video_path = os.path.join(record_dir, f'recording_{timestamp}.avi')

    width = int(data_collector.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    height = int(data_collector.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    writer = cv2.VideoWriter(video_path, fourcc, RECORD_FPS, (width, height))

    if not writer.isOpened():
        print(f'[REC] ERROR: VideoWriter open failed -> {video_path}')
        return None, None, 0

    print(f'[REC] START recording')
    print(f'[REC]   path     : {video_path}')
    print(f'[REC]   size     : {width}x{height}')
    print(f'[REC]   fps      : {RECORD_FPS}')
    print(f'[REC]   press "{RECORD_KEY}" again to stop')
    return writer, video_path, 0


def stop_recording(writer, video_path, frame_count, elapsed_sec):
    """영상 녹화 종료 및 리소스 정리."""
    if writer is not None:
        writer.release()
    avg_fps = (frame_count / elapsed_sec) if elapsed_sec > 0 else 0.0
    print(f'[REC] STOP recording')
    print(f'[REC]   path     : {video_path}')
    print(f'[REC]   frames   : {frame_count}')
    print(f'[REC]   duration : {elapsed_sec:.2f}s')
    print(f'[REC]   avg fps  : {avg_fps:.2f}')


def main():
    DATA_PATH = os.path.dirname(real_path) + '/camera_perception_pkg/camera_perception_pkg/lib/Collected_Datasets'
    CAMERA_NUM = 2
    SERIAL_PORT = '/dev/ttyACM0'
    MAX_STEERING = 7  # 사용자 정의 최대 조향 단계

    print(DATA_PATH)
    print(f'[INFO] Video record toggle key: "{RECORD_KEY}" (start/stop)')

    # 데이터 수집 객체 초기화
    data_collector = module.Data_Collect(path=DATA_PATH, cam_num=CAMERA_NUM, max_steering=MAX_STEERING)
    ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
    time.sleep(1)

    recording = False
    video_writer = None
    video_path = None
    record_frame_count = 0
    record_start_time = None
    last_record_key_pressed = False
    last_rec_log_time = 0.0

    try:
        while True:
            # v키 엣지 감지: 한 번 누를 때마다 녹화 시작/종료 토글
            record_key_pressed = keyboard.is_pressed(RECORD_KEY)
            if record_key_pressed and not last_record_key_pressed:
                if not recording:
                    video_writer, video_path, record_frame_count = start_recording(
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
            last_record_key_pressed = record_key_pressed

            # 한 번의 키보드 입력 처리
            result = data_collector.process()

            # 프로세스 종료 플래그 확인
            if result['exit']:
                steering = 0
                left_speed = 0
                right_speed = 0
                message = f's{steering}l{left_speed}r{right_speed}\n'
                ser.write(message.encode())
                break

            # 녹화 중이면 프레임을 영상으로 저장 + 디버그 로그
            if recording and video_writer is not None:
                ret, frame = data_collector.cap.read()
                now = time.time()
                if ret:
                    video_writer.write(frame)
                    record_frame_count += 1
                    # 약 1초마다 상태 로그 (터미널 디버깅용)
                    if now - last_rec_log_time >= 1.0:
                        elapsed = now - record_start_time if record_start_time else 0.0
                        control = data_collector.get_control_values()
                        print(
                            f'[REC] recording... frames={record_frame_count} '
                            f'elapsed={elapsed:.1f}s '
                            f'steer={control["steering"]} '
                            f'L={control["left_speed"]} R={control["right_speed"]} '
                            f'file={os.path.basename(video_path)}'
                        )
                        last_rec_log_time = now
                else:
                    print('[REC] WARNING: failed to read frame from camera')

            # 현재 제어 값 가져오기
            control_values = data_collector.get_control_values()

            # 시리얼 송신
            message = (
                f's{control_values["steering"]}'
                f'l{control_values["left_speed"]}'
                f'r{control_values["right_speed"]}\n'
            )
            ser.write(message.encode())

            # 디버깅용 출력
            if recording:
                print(f'[REC] Sent: {message.strip()}')
            else:
                print(f'Sent: {message.strip()}')

    except KeyboardInterrupt:
        steering = 0
        left_speed = 0
        right_speed = 0
        message = f's{steering}l{left_speed}r{right_speed}\n'
        ser.write(message.encode())
        print('Program interrupted.')
    finally:
        if recording and video_writer is not None:
            elapsed = time.time() - record_start_time if record_start_time else 0.0
            stop_recording(video_writer, video_path, record_frame_count, elapsed)
        ser.close()
        data_collector.cleanup()
        print('Serial connection closed.')


if __name__ == '__main__':
    main()
