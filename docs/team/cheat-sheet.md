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

W=$HOME/ros2_ws/weights
# 소단위 (모터 OFF) — 상세: debug-and-incremental-test.md
ros2 launch launch_pkg camera_only.launch.py cam_num:=0
./scripts/c920_setup.sh match_train /dev/video0
ros2 launch launch_pkg perception_debug.launch.py \
  model:=$W/teamop_best.pt device:=cuda:0 cam_num:=0
# 차선만 A/B: model:=$W/best_psh.pt
# 파이프라인만: model:=$W/team14_best.pt
# best_psh_v2 = Traffic 전용, 차선 없음, 주행 금지
ros2 run debug_pkg bev_calibrator_node
./scripts/run_session.sh
# 폐루프 (race는 drive_speed 없을 수 있음)
ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt device:=cuda:0
# 차선만 A/B: model:=$W/best_psh.pt
python3 src/data_collection/data_collection.py
```

`main.launch.py`: Stage1에 **serial_sender 활성**. 신호등 detector 기본 ON (`enable_traffic_light:=false`로 끔). 라이다는 주석.  
구간 테스트: [wait-green.md](wait-green.md) §6 — `/force_start` 또는 `require_green_start:=false`.  
가이드: [repo-structure-and-realcar-guide.md](repo-structure-and-realcar-guide.md) · [yolo-weights.md](yolo-weights.md) · [controller-tuning.md](controller-tuning.md) · [debug-and-incremental-test.md](debug-and-incremental-test.md)

## 가중치 스왑 · 정지 검출

```bash
W=$HOME/ros2_ws/weights
# 1) teamop (기본)  2) best_psh (차선만 A/B)
# team14는 주행 제외. best_psh_v2는 차선 없음.
# 상세·라벨 일람: yolo-weights.md §2.3·§3
ros2 topic echo /detections --once          # lane2 마스크?
ros2 topic echo /yolov8_lane_info --once    # 타겟점?
```

목록·분석: [yolo-weights](yolo-weights.md) · [teamop-vs-team14](teamop-vs-team14.md) · 참고 레포: [external-references](external-references.md)

## 디버그 토픽

```bash
ros2 topic hz /image_raw
ros2 topic echo /detections --once
ros2 topic echo /yolov8_traffic_light_info
ros2 topic echo /topic_control_signal
# 구간 테스트: 대기 중일 때 출발
ros2 topic pub --once /force_start std_msgs/msg/Bool "{data: true}"
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

- 미션: **2차선 · 반시계 2바퀴 · 4분** · 적→녹 후 **종료까지 초록** · 1랩 무장애 · 도착 차량≈출발점+**30cm**
- 정지: **차량 감지** (+논의안: **좌측 차량 AND 신호등 박스≈Npx**) · 규정집 위치 · FOV → 조기관측+라이다 백업
- 차선: **좌 점선 밟기=페널티** · **우 실선 밟기=무페널티** · **어디든 넘어가면 페널티**
- 채점: 페널티=시간 · 랩타임(+페널티) 짧은 순
- HW: **SMPS 12.0V** · 센서 ≤전후110 / 좌우60 / 높이75 cm · 제공 부품만
- 재시도 1 · 재위치 ≤3 · 페널티: a1+30 · a2/a3+50 · a4+10 · b1+15 · b2+20 · b3+10/회 · b4+30
- 상세: [rules](../06-final-eval/rules.md) · [verbal-briefing](../06-final-eval/verbal-briefing.md) · [strategy](../06-final-eval/mission-strategy.md) · [logging](../06-final-eval/logging-and-experiments.md) · [wait-green](wait-green.md)
