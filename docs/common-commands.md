# 자주 쓰는 명령어

실차·개발 때 터미널에 자주 치는 명령만 모았다.  
짧은 치트시트: [team/cheat-sheet.md](team/cheat-sheet.md) · HW 부팅: [team/hw-boot.md](team/hw-boot.md) · 소단위 디버그: [team/debug-and-incremental-test.md](team/debug-and-incremental-test.md)

실차 노트북은 **Ubuntu 22.04 + ROS2 Humble 네이티브** 기준이다 (Docker 안 씀).  
교육장 경로 `~/ros2_ws` ≈ 이 워크스페이스의 `H-Mobility-Autonomous-Advanced-Course/`.

---

## 1. ROS2 환경

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash   # 또는 cd ~/ros2_ws && source install/setup.bash

# (선택) 팀 노트북끼리 토픽 안 섞이게
export ROS_LOCALHOST_ONLY=1
# export ROS_DOMAIN_ID=14
```

터미널 열 때마다 `source`가 귀찮으면:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
# 워크스페이스 install은 경로가 바뀔 수 있어 필요할 때만 source
```

---

## 2. 장치 확인

```bash
ls -l /dev/video*
ls -l /dev/ttyACM*    # Arduino
ls -l /dev/ttyUSB*    # LiDAR 등
```

| 장치 | 흔한 이름 | 코드에서 고칠 곳 |
|------|-----------|------------------|
| 카메라 | `/dev/video0` 등 | `cam_num` / `CAMERA_NUM` |
| Arduino | `/dev/ttyACM0` | `PORT` / `SERIAL_PORT` |
| LiDAR | `/dev/ttyUSB0` 등 | lidar 포트 파라미터 |

---

## 3. 시리얼 권한 (`ttyACM0`)

`sudo chmod 777 /dev/ttyACM0`은 **임시**다. 노트북 재부팅·USB 재연결마다 장치 노드가 다시 만들어져 권한이 풀린다.

### 3-1. 영구 (권장) — `dialout` 그룹

```bash
sudo usermod -aG dialout $USER
```

**로그아웃 후 다시 로그인**(또는 재부팅)해야 적용된다.

```bash
groups                  # dialout 이 보이면 OK
ls -l /dev/ttyACM0      # 보통 root dialout, 모드 rw-rw----
```

이후 Arduino를 뽑았다 꽂아도 보통 `chmod` 없이 열린다.

### 3-2. 영구 — udev 규칙 (노트북당 1회)

`/etc/udev/rules.d/99-arduino-serial.rules` 내용 예:

```text
KERNEL=="ttyACM*", MODE="0666", GROUP="dialout"
KERNEL=="ttyUSB*", MODE="0666", GROUP="dialout"
```

```bash
sudo nano /etc/udev/rules.d/99-arduino-serial.rules   # 위 내용 저장
sudo udevadm control --reload-rules
sudo udevadm trigger
# USB 뽑았다 꽂은 뒤
ls -l /dev/ttyACM0
```

### 3-3. 임시 (급할 때만)

```bash
sudo chmod 777 /dev/ttyACM0   # 장치명에 맞게
```

Arduino IDE **시리얼 모니터**와 ROS `serial_sender`를 동시에 열지 말 것.

---

## 4. `chmod +x` vs `chmod 777`

둘 다 “권한”을 바꾸지만 **대상과 의미가 다르다**.

### 한 줄 요약

| 명령 | 무엇을 하나 | 언제 쓰나 |
|------|-------------|-----------|
| `chmod +x` / **`chmod 755`** | 실행 비트 켜기 (보통 소유 rwx, 남 r-x) | 스크립트를 `./script.sh`로 실행 |
| `chmod 777` | 전원한(`rwx`×3) | 시리얼 임시 개방 (재연결 시 풀림) |

### 숫자 한 자리 뜻

각 자리는 **소유자 / 그룹 / 기타**이고, 한 자리 안에서:

| 값 | 의미 | 기호 |
|----|------|------|
| `4` | 읽기 | `r` |
| `2` | 쓰기 | `w` |
| `1` | 실행 | `x` |
| 합 | 예: `4+2+1=7` → `rwx`, `4+1=5` → `r-x`, `4+2=6` → `rw-` |

### `chmod +x` ↔ 숫자 **`755`**

- `+x` = 실행(`x`) 비트만 **추가** (기존 r/w는 유지)
- 일반 파일 기본이 `644`(`rw-r--r--`)일 때 `chmod +x` 하면 결과가 **`755`** (`rwxr-xr-x`)
- 그래서 스크립트에 “`+x`랑 같은 숫자”라고 하면 보통 **`755`** 를 말한다

```bash
chmod +x script.sh      # 기호 방식
chmod 755 script.sh     # 숫자로 같은 목적 (일반 스크립트)
./script.sh
```

`777`은 `+x`의 대응이 **아니다**. `777`은 전원한(`rwx`×3), `755`는 “실행 가능하게 + 남에게는 쓰기만 막기”다.

### `chmod 777`

- `777` = 누구나 읽기·쓰기·실행
- 시리얼에 쓰면 당장 포트는 열리지만 USB 재연결 시 **다시 풀림** → 가능하면 `dialout` / udev

```bash
sudo chmod 777 /dev/ttyACM0   # 임시
# 읽기·쓰기만 전부 허용이면 666 (실행 비트 없음)
```

### 헷갈리기 쉬운 점

| 하고 싶은 일 | 쓸 것 |
|--------------|--------|
| 스크립트 실행 | `chmod +x` 또는 **`chmod 755`** |
| 시리얼 임시 개방 | `chmod 666` / `777` (또는 dialout·udev) |
| `+x`만으로 ttyACM 열기 | ❌ 안 됨 (장치는 읽기/쓰기 필요) |

```bash
ls -l script.sh /dev/ttyACM0
# -rwxr-xr-x  → 755, 실행 가능 스크립트
# crw-rw---- 1 root dialout → dialout이면 시리얼 OK
```

---

## 5. 빌드 · 실행

```bash
cd ~/ros2_ws
colcon build --symlink-install

# 실패 시 클린 빌드
rm -rf build install log
colcon build --symlink-install

source install/setup.bash
ros2 launch launch_pkg main.launch.py
# 인자 목록: team/launch-args.md
```

데이터 수집:

```bash
cd ~/ros2_ws
python3 src/data_collection/data_collection.py
```

수집 키: `w/s` 속도 · `a/d` 조향 · `r` 리셋 · `c` 캡처 · `v` 녹화 · `f` 종료

---

## 6. YOLO 가중치 스왑 · 검증 (자주 씀)

후보 `.pt`는 레포에 포함됨. 상세·순위: [team/yolo-weights.md](team/yolo-weights.md)

```bash
# 경로 한 번만
W=$HOME/ros2_ws/weights
ls "$W"/*.pt
```

### 6-1. 테스트 순서 (파일만 바꿔 재런치)

```bash
# 1순위 주행 기본
ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt drive_speed:=50
# 차선만 A/B
# model:=$W/best_psh.pt

# 백업
# model:=$W/youngsangc_best.pt
# model:=$W/1taekim_ti_best.pt
# model:=$W/1taekim_best.pt
# model:=$W/cms1575_best.pt   # 느릴 수 있음 (~52MB)
# team14_best.pt 는 파이프라인 확인만 (주행 제외)
# best_psh_v2.pt / hlhl_* 는 차선 드롭인 금지

# 순위 근거: team/yolo-weights.md §3
```

### 6-2. 저속 · threshold 조절

```bash
ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt drive_speed:=50

ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt drive_speed:=40
# threshold 는 main 인자가 아니다. 띄운 뒤 바꾼다:
#   ros2 param set /yolov8_node threshold 0.4

ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt drive_speed:=60
```

### 6-3. 정지 검출 합격 체크 (매 가중치마다)

```bash
ros2 topic hz /image_raw
ros2 topic echo /detections --once          # lane2 마스크 · traffic_light?
ros2 topic echo /yolov8_lane_info --once    # 타겟점 나오는지
ros2 topic echo /topic_control_signal --once
```

시각화 노드가 떠 있으면 RViz/`yolov8_visualizer`로 마스크 확인.  
통과 기준: `lane2` 세그 + `/yolov8_lane_info` 타겟점 → 저속 1바퀴.

**Colab 재학습/파인튜닝은 위 드롭인이 조명·각도에서 깨질 때만** (같은 Kingo로 밤샘 학습은 이득 거의 없음).  
정의·실패 시트·워크플로: [team/yolo-weights.md §4](team/yolo-weights.md).

### 6-4. 소단위 스테이지 (serial 없이 먼저)

상세: [team/debug-and-incremental-test.md](team/debug-and-incremental-test.md)

```bash
# 1) 카메라만
ros2 launch launch_pkg camera_only.launch.py cam_num:=0

# 2) C920e — 포커스 잠금, AE/AWB auto (전부 픽스하지 말 것)
./scripts/c920_setup.sh match_train /dev/video0

# 3) 인지 (모터 없음)
ros2 launch launch_pkg perception_debug.launch.py \
  model:=$W/teamop_best.pt cam_num:=0

# 4) IPM 트랙바 (인지 launch 뜬 채)
ros2 run debug_pkg bev_calibrator_node   # p=출력 s=저장

# 5) 세션 bag
./scripts/run_session.sh

# 6) 폐루프 + race_viz (debug:=true 가 기본)
ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt drive_speed:=50

# 7) 라이다만 확인 (모터·시리얼 없음)
ros2 launch launch_pkg sensor_bag.launch.py lidar:=true

./scripts/topic_rates.sh
python3 tools/dump_bev.py /tmp/bev.png
python3 tools/dump_roi.py /tmp/roi.png
```

---

## 7. 디버그 (토픽)

```bash
ros2 topic list
ros2 topic hz /image_raw
ros2 topic echo /detections --once
ros2 topic echo /topic_control_signal
ros2 topic echo /yolov8_lane_info
ros2 node list
```

---

## 8. Git (팀 작업)

```bash
cd ~/ros2_ws
git status
git pull
git add -A
git commit -m "메시지"
git push
```

실차 후보 `.pt`는 레포 루트 [`weights/`](../weights/)에 둔다 ([team/yolo-weights.md](team/yolo-weights.md)). 원격 push는 팀 합의 후(용량·LFS).

---

## 안전 한 줄

조교 확인 전 배터리 OFF · SMPS **12.0V** · 시리얼 모니터 끄고 ROS/수집 · 핫플러그로 장치명 꼬이지 않게 USB 정리
