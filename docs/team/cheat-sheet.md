# 치트시트 — 명령 · 핀 · 키맵

## 환경

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash   # 또는 ./install/setup.bash
export ROS_LOCALHOST_ONLY=1          # 팀 정책에 따라
# export ROS_DOMAIN_ID=14
```

## 장치

```bash
ls /dev/video*
ls /dev/ttyACM*
ls /dev/ttyUSB*
sudo chmod 777 /dev/ttyACM0
```

## 빌드 · 실행

```bash
cd ~/ros2_ws
colcon build --symlink-install
# 실패 시: rm -rf build install log && colcon build --symlink-install

W=$HOME/ros2_ws/src/camera_perception_pkg/camera_perception_pkg/weights
ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt device:=cuda:0 drive_speed:=50
# 교체: youngsangc_best.pt → 1taekim_best.pt → 1taekim_ti_best.pt → cms1575_best.pt
python3 src/data_collection/data_collection.py
```

`main.launch.py`: Stage1에 **serial_sender 활성**. 신호등·라이다는 미션 시 주석 해제.  
가이드: [repo-structure-and-realcar-guide.md](repo-structure-and-realcar-guide.md) · [yolo-weights.md](yolo-weights.md)

## 가중치 스왑 · 정지 검출

```bash
W=$HOME/ros2_ws/src/camera_perception_pkg/camera_perception_pkg/weights
# 1) teamop → 2) youngsangc → 3) 1taekim → 4) cms1575
ros2 topic echo /detections --once          # lane2 마스크?
ros2 topic echo /yolov8_lane_info --once    # 타겟점?
```

목록·분석: [yolo-weights](yolo-weights.md) · 참고 레포: [external-references](external-references.md)

## 디버그 토픽

```bash
ros2 topic hz /image_raw
ros2 topic echo /detections --once
ros2 topic echo /topic_control_signal
```

## Arduino 핀 (`driving.ino`)

| 기능 | 핀 |
|---|---|
| 조향 IN1/IN2 | 2 / 3 |
| 우 후륜 IN1/IN2 | 5 / 4 (`FORWARD_RIGHT_1/2`) |
| 좌 후륜 IN1/IN2 | 6 / 7 |
| 가변저항 | A2 |
| baud | 115200 |

## 수집 키

`w/s` 속도 · `a/d` 조향 · `r` 리셋 · `c` 캡처 · `v` 녹화 · `f` 종료

## 안전 한 줄

조교 확인 전 배터리 OFF · SMPS +V=붉은/9-36V, −V=검/PGND · 모터는 OUT1/OUT2만 · 시리얼 모니터 끄고 ROS/수집

## 주행 평가 (ver3.3 + 구두 가규정)

- 미션: **2차선 · 반시계 2바퀴 · 4분** · 적→녹 출발(이후 초록 유지 기본) · 1랩 장애물 없음 · 도착 차량≈출발점+**30cm**(1차로 1대)
- 정지: **규정집**(앞바퀴 선 앞·뒷바퀴 선 뒤) · 물체탐지 정석·수단 자유 · FOV 상실 → 조기관측+라이다 · **랩2 적불 여부 내일 확인**
- 채점: 페널티=시간 가산 · 랩타임(+페널티) 짧은 순 · 침범·이탈 모두 페널티
- HW: **SMPS 12.0V** · 센서 ≤전후110 / 좌우60 / 높이75 cm · 제공 부품만
- 재시도 1 · 재위치 ≤3 · 페널티: a1+30 · a2/a3+50 · a4+10 · b1+15 · b2+20 · b3+10/회 · b4+30
- 상세: [rules](../06-final-eval/rules.md) · [verbal-briefing](../06-final-eval/verbal-briefing.md) · [strategy](../06-final-eval/mission-strategy.md) · [logging](../06-final-eval/logging-and-experiments.md)
