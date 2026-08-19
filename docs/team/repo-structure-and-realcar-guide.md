# H-모빌리티 레포 구조와 내일 실차 단계별 가이드 (14팀)

목적: 코드를 “어디에 손대면 차가 나가는지”만 잡고, 실차에서 바로 실험할 수 있게 머리 속 지도를 그린다.

관련: [tomorrow-prep.md](tomorrow-prep.md) · [cheat-sheet.md](cheat-sheet.md) · [yolo-weights.md](yolo-weights.md) · [teamop-vs-team14.md](teamop-vs-team14.md) · [controller-tuning.md](controller-tuning.md) · [debug-and-incremental-test.md](debug-and-incremental-test.md) · [external-references.md](external-references.md) · [lowspeed-tuning.md](lowspeed-tuning.md)

---

## 0. 큰 그림 — 워크스페이스는 세 갈래

상위 폴더 `2026-H-Mobility-Class/`:

```text
2026-H-Mobility-Class/
├── H-Mobility-Autonomous-Advanced-Course/              ← 실차·오프라인 (내일의 주 무대)
├── H-Mobility-Autonomous-Advanced-Course-Simulation/   ← Gazebo 시뮬
└── docker/                                             ← ROS2 Humble 실행 환경
```


| 갈래              | 언제 쓰나                 | 핵심 명령                                              |
| --------------- | --------------------- | -------------------------------------------------- |
| **Course (실차)** | 노트북 ↔ 카메라·Arduino·라이다 | `ros2 launch launch_pkg main.launch.py`            |
| **Simulation**  | 트랙 알고리즘을 안전하게 검증      | `ros2 launch simulation_pkg driving_sim.launch.py` |
| **Docker**      | 호스트에 Humble이 없을 때     | `hmobility-offline` / `hmobility-sim`              |


시뮬에서 잘 도는 인지·제어 개량본과 실차용 교육 베이스라인은 **패키지 이름은 같지만 내용이 다르다**.  
내일은 **Course**를 기준으로 하고, 시뮬에서 배운 “차로 중심 추종 + 속도/조향 튜닝” 감각만 가져간다.

---



## 1. 자율주행 파이프라인 — 눈 → 길 → 핸들

```text
카메라 (image_raw)
  → yolov8_node              [가중치 best.pt]
  → lane_info_extractor      [차로 중심]
  → path_planner             [스플라인 경로]
  → motion_planner           [조향·좌우 속도]
  → serial_sender            [Arduino s/l/r]
  → 차량
```


| 단계    | 노드                         | 여러분이 손댈 일                                            |
| ----- | -------------------------- | ---------------------------------------------------- |
| 인지    | `yolov8_node`              | **가중치** `best.pt`, conf, device                      |
| 차로    | `lane_info_extractor_node` | BEV/오프셋 (실차는 대부분 `.pyc` lib)                         |
| 경로    | `path_planner_node`        | 거의 고정                                                |
| 제어    | `motion_planner_node`      | **속도·조향 제한** ([lowspeed-tuning](lowspeed-tuning.md)) |
| 액추에이터 | `serial_sender_node`       | 포트 `/dev/ttyACM0`, 권한                                |




### 토픽 (디버깅용으로 이름만 기억)


| 단계  | 토픽                          | 메시지                |
| --- | --------------------------- | ------------------ |
| 센서  | `image_raw`                 | Image              |
| 인지  | `detections`                | DetectionArray     |
| 차로  | `yolov8_lane_info`          | LaneInfo           |
| 계획  | `path_planning_result`      | PathPlanningResult |
| 제어  | `topic_control_signal`      | MotionCommand      |
| 신호등 | `yolov8_traffic_light_info` | String             |
| 장애물 | `lidar_obstacle_info`       | Bool               |


확인 예:

```bash
ros2 topic list
ros2 topic hz /image_raw
ros2 topic echo /detections --once
ros2 topic echo /topic_control_signal
```

---



## 2. 실차 레포 구조 (Course `src/`)


| 패키지                        | 역할                         |
| -------------------------- | -------------------------- |
| `launch_pkg`               | `main.launch.py`로 노드 일괄 기동 |
| `camera_perception_pkg`    | 카메라, YOLO, 차로, 신호등         |
| `decision_making_pkg`      | path / motion              |
| `serial_communication_pkg` | MotionCommand → Arduino    |
| `lidar_perception_pkg`     | 스캔·장애물 Bool (종료 정지·미션)     |
| `interfaces_pkg`           | 커스텀 메시지                    |
| `debug_pkg`                | 시각화 · IPM 트랙바 · HUD · 라이다 top-down · 마커 ([debug-and-incremental-test](debug-and-incremental-test.md)) |
| `control/`                 | Arduino `driving.ino` 등    |
| `data_collection/`         | YOLO 학습용 프레임/영상 수집         |


**숙제 세 가지:** (1) 트랙에 맞는 YOLO 가중치 (2) launch에서 실차 노드 켜기 (3) 속도·조향이 실차에 안전한지 확인.

---



## 3. Course vs Simulation


|        | Course (실차)                 | Simulation       |
| ------ | --------------------------- | ---------------- |
| 입력     | USB 카메라 노드                  | Gazebo 카메라       |
| 가중치    | `best.pt` (직접 학습)           | `sim.pt`         |
| 제어 출력  | 시리얼 → Arduino               | `/cmd_vel`       |
| 코드 성숙도 | 교육용 베이스 + `.pyc` lib        | 팀 개량 lane/motion |
| 실행     | 현장 PC / `hmobility-offline` | `hmobility-sim`  |


`sim.pt`를 실차에 그대로 쓰지 말 것 — 도메인(텍스처·조명·카메라)이 다르다.

---



## 4. 대회 트랙 요구 (한 줄)

- **2차선 · 반시계 · 2바퀴 · 4분**
- **초록 신호 후** 출발 · 종료 시 **물체 탐지 후 정지**
- HW: SMPS **12.0V**, 센서 치수 제한, 제공 부품만
- 도로 폭 850 mm — “빨리”보다 “차로 중앙 유지”가 먼저

상세: [06-final-eval/rules.md](../06-final-eval/rules.md) · [dev-checklist.md](../06-final-eval/dev-checklist.md)

---



## 5. 실차 작업 순서 (권장)



### Step A — 도착 직후 하드웨어 ([tomorrow-prep](tomorrow-prep.md))

장치명 · 시리얼 권한 · SMPS 12.0V · 가변저항 끝값.

### Step B — 데이터 → YOLO ([yolo-weights](yolo-weights.md))

**기본:** 루트 [`weights/`](../../weights/)의 **`teamop_best.pt`**. `best_psh.pt`는 차선만 A/B(신호등 약함). `best_psh_v2`는 차선 없음. `team14_best.pt`는 파이프라인 확인만. 순서: [yolo-weights §3](yolo-weights.md).  
참고 레포 URL·clone: [external-references](external-references.md).  
안 되면 Colab+Roboflow [`notebooks/kingo_car.ipynb`](notebooks/kingo_car.ipynb).  
정지 상태에서 마스크가 붙는지 먼저 확인.

### Step C — 소단위 검증 후 Launch

**한 번에 main 을 켜지 말 것.** 순서: 카메라 → C920e → 인지(serial OFF) → IPM 트랙바 → 저속 폐루프.  
상세 명령: [debug-and-incremental-test.md](debug-and-incremental-test.md)

`main.launch.py`에서 `serial_sender`**는 실차 주행용으로 활성화**되어 있다 (`data_source` 기본=`camera`).  
신호등·라이다 노드는 `main.launch.py`에서 **항상 켜진다.** 시각화는 `debug:=true`(기본)의 `race_viz` 한 창.

시리얼 모니터(Arduino IDE)와 ROS `serial_sender`를 **동시에** 열지 말 것.

### Step D — 정지 디버깅 → 저속 ([lowspeed-tuning](lowspeed-tuning.md))

인지 → 저속 직선 → 코너 → 그다음 속도·미션.

### Step E — 규정 체크

초록 출발 · 2차선 · 랩타이머 회피 · 2바퀴 후 정지선 정지.

피해야 할 네 가지: **조기 출발 · 이탈 · 스톨 · 랩타이머 충돌**.

---



## 6. 명령 치트

```bash
# 환경
source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash

# 빌드 · 주행
cd ~/ros2_ws
colcon build --symlink-install
ros2 launch launch_pkg main.launch.py
# 가중치 교체 예:
# ros2 launch launch_pkg main.launch.py model:=best.pt

# 데이터 수집
python3 src/data_collection/data_collection.py
```

Arduino `driving.ino`: `s{조향}` `l{좌}` `r{우}`, 가변저항 A2, 115200.

---



## 7. 내일 우선순위 (한 장)

1. 장치·전원·시리얼이 살아 있는가
2. 우리 트랙 데이터로 만든 YOLO가 차선을 잡는가
3. `serial_sender`가 켜져 차가 명령에 반응하는가
4. 저속으로 차로를 따라가는가 (속도는 나중에)
5. 신호등·2바퀴·종료 정지 (미션 완성)

먼저 “느려도 이탈 없이”를 만들고, 그다음이 기록이다.