# 공개 참고 레포 · 자료 (실차 노트북용)

목적: Course만 `git pull`한 상태에서도 **원본 URL로 클론**해 인지·제어를 참고한다.  
이 문서는 `external/` 클론을 **하나씩 열어** 2026 H-모빌리티(화학관 라운지)에 **실제로 쓸 점 / 복사하면 안 되는 점**을 정리한 것이다.

가중치 드롭인·테스트 순서: [yolo-weights.md](yolo-weights.md)  
이미 복사된 `.pt`: [`weights/`](../../src/camera_perception_pkg/camera_perception_pkg/weights/)  
소단위 검증: [debug-and-incremental-test.md](debug-and-incremental-test.md)

**우리 스택 (바꾸지 말 것):** `lane2` + `traffic_light` YOLO-seg → HSV 색 → bang-bang `motion_planner` → Arduino `s{steer}l{left}r{right}\n` **115200**.  
**미션:** `WAIT_GREEN` → CCW 2랩 → 랩2 1차로 정차 차량에서 정지. 주차·차선변경은 필수가 아님.  
**HW:** C920e, i7+RTX 3050 → `device:=cuda:0`.

작업 트리는 계속 `~/ros2_ws`(Course). 실차에서 참고 클론은 **`~/ref`** (ros2_ws 밖). 개발 PC의 `external/` 과 같은 역할이다.

---

## 0. 내일 한 장 — 어디서 뭘 가져오나

어느 레포에도 **랩 카운트 FSM / 완성된 WAIT_GREEN** 은 없다. 출발 게이트·랩 구분은 Course `motion_planner`에 **우리가 넣는다**.

| 우선 | 가져올 것 | 출처 |
|:---:|-----------|------|
| P0 | `lane2`/`traffic_light` 가중치 | **teamop_best** (기본) → best_psh (차선 A/B, TL 약함) → youngsangc → 1taekim_ti → cms1575. team14·psh_v2는 주행 제외 |
| P0 | bang-bang 시작 숫자: `steer +5/−6`, speed 50→160 | 1TAEKIM |
| P0 | 초록이 될 때까지 속도 0 | cms1575 `traffic_stop`↔`green` **아이디어만** |
| P0 | LiDAR 전방 0–30°, 0.5–2 m, `consec_count=5` | Course/PCC 기본. 장착 후 각도만 스윕 |
| P1 | 직선/코너 속도 분기 (180/165) | youngsangc |
| P1 | 랩2 정지: bbox 크기 + LiDAR AND | cms1575 `lane2_car` 패턴 (클래스명은 우리 검출에 맞게) |
| P1 | serial 재연결·종료 시 0 전송 | PCC `serial_sender` |
| P1 | 동일 트랙 신호등 latch·runbook | F23 **문서만** |
| P2 | arctan 조향 / PID path | TeamOP / HLHL — 1바퀴 안정 후 |
| — | F23 `.pt`, HLHL `lane` 클래스, PCC `cls_name='lane'`, serial 9600, speed 255 | **복사 금지** |

로컬 클론 경로: 워크스페이스 `external/<폴더>/`.

```bash
mkdir -p ~/ref && cd ~/ref
git clone --depth 1 https://github.com/hyeyeonIm/TeamOP.git
git clone --depth 1 https://github.com/cms1575/autonomous_vehicle_SKKU.git
git clone --depth 1 -b driving-obstacle-avoidance \
  https://github.com/x2-qp-cheese/skku-ai-autonomous-driving-2026.git f23-driving
```

---

## 1. 한눈 비교 (공식 Course 대비)

| | IPM | 제어 | speed | path 노드 | TL | LiDAR 각도/거리/consec | 드롭인 `.pt` |
|--|-----|------|-------|-----------|-----|------------------------|--------------|
| **Course (우리)** | stock / 300 | bang-bang ±7 | 60 param | O | HSV | 0–30° / 0.5–2 m / 5 | `weights/` |
| **TeamOP** | stock / 300 | arctan+d_error | **255** | X | HSV | 80–150° / 0.1–1.2 m / 5 | `teamop_best.pt` |
| **youngsangc** | stock / 300 | slope×0.1 | 180/165/50 | X | HSV | 75–110° / 0.5–1 m / 5 | `youngsangc_best.pt` |
| **1TAEKIM** | stock / 300 | bang **+5/−6** | **160** | X | HSV | **80–90°** / 0.3–1 m / **1** | `1taekim_*.pt` |
| **HLHL** | 커스텀 / 200 | PID+LPF | 100 | O | YOLO 색 클래스 | 0–30° (launch off) | `hlhl_*` **차선 비호환** |
| **cms1575** | stock / 300 | bang+deadband / FSM | 150–255 | O | HSV | 주차용 270–275° | `cms1575_best.pt` |
| **PCC ros3** | stock / 300 | P-gain | 100/60 | O | HSV | 0–30° / 0.5–2 m / 5 | ONNX **`lane` 금지** |
| **F23 driving** | ratio BEV | path gain | 255 | (비ROS) | HSV+latch | 330–30° / 0.3 m | **클래스 다름 금지** |

stock IPM = `[[238,316],[402,313],[501,476],[155,476]]`. 우리 카메라각이 다르면 [bev_calibrator](debug-and-incremental-test.md)로 덮어쓴다. 남의 `src_mat`를 검증 없이 넣지 말 것.

---

## S — 공식 클래스 (`lane2` + `traffic_light`)

### TeamOP — `hyeyeonIm-TeamOP`

- 원본: [hyeyeonIm/TeamOP](https://github.com/hyeyeonIm/TeamOP)  
  `git clone --depth 1 https://github.com/hyeyeonIm/TeamOP.git`
- H-모빌리티 14기. 병합셋 `H_merge_all` → 우리 `weights/teamop_best.pt` (공개 기준점). Kingo-only는 `team14_best`이며 실차에선 더 약함 ([teamop-vs-team14.md](teamop-vs-team14.md)). 팀원 `best_psh.pt`는 YOLO11s-seg라 TeamOP와 별개.
- `path_planner` 없음. lane → motion 직결.
- 조향: `B_max=8`, `kp=0.07`, `kd=2`, arctan + 미분 억제. Course bang-bang과 **구조가 다름**.
- 속도 **255 고정** — 내일 그대로 쓰지 말 것. 저속 50부터.
- Red 정지 `y_max < 154` (우리 150과 비슷).
- LiDAR `80–150°`, `0.1–1.2 m`, consec 5 — 보넷 장착 후 각도 후보.
- HSV는 우리 Course와 거의 동일 (`S,V` 하한 100 vs 우리 95).
- **WAIT_GREEN / 랩 FSM 없음.**
- 적용: 가중치 P0. arctan은 코너가 흔들릴 때 P2 옵션.
- 금지: speed 255, path_planner 제거.

파일: `src/decision_making_pkg/.../motion_planner_node.py`, `src/lidar_perception_pkg/.../lidar_obstacle_detector_node.py`.

### youngsangc — `youngsangc-H-Mobility-Autonomous-Advanced-Course`

- 원본: [youngsangc/H-Mobility-Autonomous-Advanced-Course](https://github.com/youngsangc/H-Mobility-Autonomous-Advanced-Course)
- `best.pt` → `youngsangc_best.pt`. 클래스 호환.
- 조향 `int(tar_slope * 0.1)`. **직선 180 / 코너 165 / 차선없음 50**.
- `car_center` 직선 `(320,179)` · 코너 `(290,179)`.
- Red `y_max < 200` — 너무 일찍 멈출 수 있음. 우리 150을 기본으로 두고 스윕만.
- LiDAR `75–110°`, `0.5–1.0 m`, consec 5.
- `yolov8_node` 기본 **`device=cpu`** — 우리는 반드시 `cuda:0`.
- 적용: 가중치 P0. **코너 감속 분기** P1 (`abs(steer)<=1`이면 직선 속도).
- 금지: cpu 추론, `y_max<200` 그대로, slope×0.1을 bang-bang 대신 첫 주행에 넣기.

### 1TAEKIM — `1TAEKIM-H-Mobility-Autonomous-Advanced-Course`

- 원본: [1TAEKIM/H-Mobility-Autonomous-Advanced-Course](https://github.com/1TAEKIM/H-Mobility-Autonomous-Advanced-Course)
- `best.pt` / `ti_best.pt` → `1taekim_best.pt`, `1taekim_ti_best.pt`.
- **우리 bang-bang과 가장 가깝다:** steer **+5 / −6**, speed **160**, `car_center=(376, 179)` (ROI 자른 뒤 범퍼 중앙 주석).
- `target_point_y=90` (우리 extractor는 5~155 step 50 — lookahead가 짧으면 코너 반응이 빠름).
- LiDAR **80–90°**, **0.3–1.0 m**, **`consec_count=1`** — 민감. 오탐으로 급정거 가능. 쓸 거면 consec **3–5**.
- Red `y_max < 200`.
- 적용: 가중치 P0. **조향 ±5/6 · speed 50→160** P0. car_center/target_y는 IPM 맞춘 뒤 P1.
- 금지: consec=1 그대로, path_planner 제거.

### HLHL — `gustj5092-HLHL`

- 원본: [gustj5092/HLHL](https://github.com/gustj5092/HLHL)
- **차선 클래스 `lane` (not `lane2`)**. extractor `cls_name='lane'`. 우리 `lane_info_extractor`에 **드롭인 금지**.
- `best_new.pt` → `hlhl_best_new.pt` (약함·백업 테스트만).
- `best_traffic_light.pt` → `hlhl_traffic_light.pt`: 색을 YOLO 클래스(`red`/`green`…)로. 우리는 **박스+HSV가 Plan A**. TL이 약할 때 2nd opinion (P2).
- IPM `[[270,184],[364,184],[635,414],[2,352]]`, `cutting_idx=200` — **그들 카메라**. 우리 C920e에 그대로 넣지 말 것. 트랙바로 새로 맞춤.
- PID `kp=30 kd=2`, lookahead 50, speed 100, steer LPF 0.15. msg에 left/right lane points — **인터페이스 확장 필요**.
- detector는 `red` 소문자, motion은 `'Red'` 비교 → **그들 코드에도 버그 가능**.
- 적용: visualizer/`roi_image` 아이디어는 이미 우리 `debug_pkg`에 있음. PID 전체는 P2.
- 금지: `lane` 가중치+우리 extractor, HLHL `src_mat` blind copy, 당일 스택 통째 교체.

---

## A — 화학관 라운지 동일 트랙 (2026 교내 · F23)

### F23 driving — `x2-qp-cheese-skku-ai-autonomous-driving-2026-driving`

- 원본: [driving-obstacle-avoidance](https://github.com/x2-qp-cheese/skku-ai-autonomous-driving-2026/tree/driving-obstacle-avoidance)  
  `git clone --depth 1 -b driving-obstacle-avoidance https://github.com/x2-qp-cheese/skku-ai-autonomous-driving-2026.git`
- **동상. 같은 라운지.** 다만 **ROS2 Course가 아님** (단독 Python).
- 클래스: `lane-center`, `lane-side`, `crosswalk`, `light`, `obstacle`. **`lane2` 필터 불가. `.pt` 드롭인 금지.**
- 시리얼: `DRIVE {speed} {steer}\n` / `STOP\n` — 우리 `s/l/r` **비호환**. 펌웨어 섞지 말 것.
- 카메라 1280×720 MJPG — 우리는 640×480.
- **그래도 읽을 것 (P1 문서):**
  - `docs/competition_notes.md` — CCW 2랩·4분·적→녹 출발
  - `docs/competition_day_runbook.md` — 당일 체크
  - `src/skku_autocar/perception/traffic_light.py` — HSV `min_sat/val=90`, **confirm_frames**, 횡단보도가 stop line(`y_ratio=0.82`)을 지나기 전에는 적 브레이크로 안 봄 → **랩 중 red 오인 방지 아이디어**
  - LiDAR 전방 래핑 `330–30°`, `stop_distance_mm=300` (`configs/default.json`)
- 디버그: `scripts/bev_tune.py`, `camera_check.py` — 우리 `bev_calibrator`/`c920_setup`과 역할이 겹침.
- 금지: `best_v1.pt`/`best_v2.pt`, `yolo_drive_app.py` 통째, `DRIVE` 프로토콜, 1280 BEV 비율을 우리 `src_mat`에 대입.

### F23 main — `x2-qp-cheese-skku-ai-autonomous-driving-2026-main`

- 개요·주차 브랜치 안내. YOLO 주행 코드는 driving 클론에 있음.
- 적용: 규정/일정 문서만. 코드 가치 낮음.

---

## B — 동일 Autolab ROS2 스택

### cms1575 — `cms1575-autonomous_vehicle_SKKU`

- 원본: [cms1575/autonomous_vehicle_SKKU](https://github.com/cms1575/autonomous_vehicle_SKKU)
- `best.pt` → `cms1575_best.pt` (m-seg ~52 MB, 느릴 수 있음). 코드상 클래스 `lane2`, `traffic_light`, 추가로 `lane1`, `lane2_car`, `lane1_car`, `jucha`.
- IPM·HSV는 우리와 **같은 숫자**.
- **가장 쓸 만한 제어 아이디어 (P0–P1):**
  - `MODE_SELECT` 의 obstacle FSM: bbox height>65 이고 **red** → 정지, **green** → 재출발. 우리는 Red만 보고 Green 대기가 약함 → **WAIT_GREEN에 이 패턴**.
  - 랩2 정지 퓨전 힌트: 차량 클래스 bbox 크기 + `lidar_obstacle_info` AND. (우리 가중치에 `lane2_car`가 없으면 `traffic_light` 정면 재접근 + LiDAR로 대체.)
- driving 모드: slope deadband ±13, steer ±2 스텝, max ±7/8, 차선변경 쿨다운 16 s — **이번 미션의 차선변경과 무관**.
- LiDAR 기본이 **주차 각도 270–275°**. 전방 정지용이 아님. 주석의 0–30° 예시를 전방 장착에 쓸 것.
- serial **9600** — 우리는 **115200**. 형식 `s/l/r` 만 같음.
- `yolov8_node` 기본이 `parking.pt`인 경우 있음. 주행은 `best.pt`.
- 금지: parking FSM 통째, 9600, POT 끝값(그들 540/394 vs 우리 실측), obstacle 차선변경 통째.

파일: `src/decision_making_pkg/.../motion_planner_node.py` (`MODE_SELECT`, `traffic_light_stop_threshold=65`).

### PCC ros3_ws — `AUTONOMOUS-PCC-Inc-ros3_ws`

- 원본: [AUTONOMOUS-PCC-Inc/ros3_ws](https://github.com/AUTONOMOUS-PCC-Inc/ros3_ws)
- **`cls_name='lane'`**, TRT `NAMES={0:"lane"}`. 우리 extractor는 `lane2`. **ONNX/engine 드롭인 금지.**
- 적용할 것:
  - serial **115200**, 포트 실패 재연결, 종료 시 `0,0,0` (P1)
  - LiDAR 0–30°, 0.5–2.0 m, consec 5 — Course 기본과 같음. 장착 확인용.
  - `bev_calibrator.py` 워크플로 — 이미 우리 `bev_calibrator_node`
  - 펌웨어 `COMMAND_TIMEOUT=500 ms` 무명령 시 속도 0 — `driving.ino`에 넣을지 검토 (P2). POT/MAX_STEER 숫자는 그들 것.
- P 제어 `STEERING_GAIN=0.2`, `BASE_SPEED=100` — bang-bang 확정 전엔 넣지 말 것.
- 금지: `lane` 가중치, TRT 노드 클래스 하드코딩.

### LSCskywalker-automobile

- `lane2` extractor, 루트 `best.pt`. Course에 **아직 안 복사**됨. 드롭인이 약하면 `external/.../best.pt` A/B (P1).
- 조향 slope×9/80 clamp ±9, 속도 **255**. Red `y_max<150`, LiDAR 0–30°.
- 적용: 단순 베이스라인 참고. 255/±9는 저속 뒤에.
- 금지: 풀 PWM 첫 주행.

### CCG-creator-autonomous-capstone-design

- 확장 클래스(`crosswalk` 등) + P제어 + 차선전환 1.5 s. Red를 `traffic_light_red` 클래스로 쓰는 분기가 있으면 우리 HSV String과 **불일치**.
- 적용: 아이디어만 (횡단보도 정지 시간). 통째 이식 X.
- `best_no_sunlight.pt` — 커튼/창 조건 FT 참고 (클래스 확인 후).

### Snowor1d-2025_jacapdi2

- `LANE2_CLASS_NAME="lane2"`. `best.pt` + `sim.pt` (시뮬 금지).
- path_planner가 큰 신호등 bbox로 lane1↔lane2 토글 — **차선변경 미션용**. 우리는 2차로 유지가 기본.
- LiDAR 0–30°, 0.5–2 m, consec 5. HSV 범위 Course와 동일.
- 적용: 라이다/HSV 확인용. 차선 토글은 넣지 말 것 (페널티).
- 시뮬 launch는 우리 Simulation 레포가 이미 있음.

### yax_jeju — `2021145074-maker-yax_jeju`

- 차선/콘/신호 **분리 가중치**, PID, `mission_controller` 우선순위 obstacle > lane.
- GPS/터널 의존. **FSM 우선순위 패턴만** P2 (랩2 정지 게이트).
- YDLidar `stop_distance_m=0.5` — 우리 RPLidar와 드라이버가 다를 수 있음.

### yunss01-dynamic_obstacle_modularization

- 전/후진 토글·주차. **이번 미션 SKIP.**

### SKKU-Auto-Drive-2024 / jaeinjaein

- 2024 캠프. jaeinjaein은 `.pt` 없고 ROS2 모노리스 아님, 클래스 left/right+색 검출.
- Auto-Drive-2024는 `lane2` seg만, 신호등 파이프 없음. 조향 스니펫만.
- **SKIP** (가중치 벤치·조향 참고 외).

---

## 교육·규정·시뮬 (공식 인접)

| 폴더 | 적용 | 스킵 |
|------|------|------|
| `SKKUAutoLab-Competition-Based-Framework_ReplicationPackage` | 규정 PDF·워크숍·유튜브 플레이리스트 | 코드는 Course 중복 |
| `SKKUAutoLab-ros2_autonomous_vehicle_book` | — | Course와 동일 교재 |
| `SKKUAutoLab-ros2_autonomous_vehicle_simulation` | Gazebo `mission_sim` (이미 우리 Simulation 레포) | `sim.pt` 실차 |
| `SKKUAutoLab-Autonomous-Driving-AI-SW-Design` | `sw_verification_node` — 카메라/시리얼/LiDAR 팝업 (첫 연결일) | 주행 로직 없음 |
| `hyeyeonIm-SJSU_DATA` | `kingo_car.ipynb` → Course `docs/team/notebooks/` (키는 팀 계정) | 주행 코드 없음 |
| `thisisWooyeol-Traffic-Light-Intersection-Task` | HSV를 **원형 렌즈 ROI**로 자르는 아이디어 (노란 하우징 오탐) | ROS1, `best_0803.pt` 미포함, COCO 클래스 |

---

## 레포가 아닌 자료

| 종류 | 링크 | 메모 |
|------|------|------|
| Roboflow Kingo Car | [kingo-car-1z3da](https://universe.roboflow.com/hyeyeonim-r19sp/kingo-car-1z3da) | 라벨드. `team14_best`·`1taekim_ti`는 Colab `Kingo-Car-1`(주행 비권장). `teamop`는 `H_merge_all-1`(실차 공개 기준점). `best_psh`는 `/content/dataset`만 남아 Kingo 여부는 미확인. [yolo-weights.md](yolo-weights.md) |
| Kaggle 시뮬 이미지 | [skkuhhk/…](https://www.kaggle.com/datasets/skkuhhk/ros2-autonomous-vehicle-simulation) | 라벨 없음 · 실차 조도/색과 달라 **우선순위 낮음** |
| HF 시뮬 가중치 | [gogoring/simulation_ws](https://huggingface.co/gogoring/simulation_ws) | `sim.pt` **실차 금지** |
| 제4회 SKKU AI 안내 | [oopy](https://studentsuccess.oopy.io/36c91056-74bf-80e7-8edb-d074d75ca1c7) | 교내 대회 (F23) |
| H-모빌리티 공식 `2026` | [SKKUAutoLab/…/tree/2026](https://github.com/SKKUAutoLab/H-Mobility-Autonomous-Advanced-Course/tree/2026) | 우리 Course의 업스트림 |
| 제2회 SW경진대회 유튜브 | [watch](https://www.youtube.com/watch?v=hmLsHTXk_fI) | 2024.07.19 화학관 |
| Autolab 워크숍 / 캡스톤 | [워크숍](https://youtube.com/playlist?list=PLIyoAG_PPqRdchsJlDibNFsI55hPlu30l) · [캡스톤1](https://www.youtube.com/playlist?list=PLIyoAG_PPqRfhqFnaGwwP4ROqpAk9VcMI) · [캡스톤2](https://www.youtube.com/playlist?list=PLIyoAG_PPqRemDN7lFsWcU-SAKQBk8Tfe) | |

---

## 우리가 직접 짜야 하는 것 (레포에 없음)

1. **WAIT_GREEN** — 첫 초록 확정 전 속도 0. 랩 중 `Red`로 다시 대기 상태로 돌아가지 말 것 ([mission-strategy.md](../06-final-eval/mission-strategy.md)).
2. **랩 카운트** — 색 변화로 세지 말 것. 신호등 정면 통과 횟수(+시간 보조).
3. **랩2 정지** — 1차로 차량(출발+~30 cm) + LiDAR. YOLO Bool만으로 최종 정지하지 말 것.
4. **C920e `match_train`** — 포커스만 잠금 ([debug-and-incremental-test.md](debug-and-incremental-test.md)).

---

## 권장 참고 순서 (현장)

1. Course `weights/` S급 드롭인 + `perception_debug` ([yolo-weights.md](yolo-weights.md))
2. 1TAEKIM 조향/속도 숫자로 저속 1바퀴
3. cms1575 아이디어로 Green 게이트 · (필요 시) 정지 퓨전
4. PCC serial 안정화 · LiDAR 0–30° 시각화 (`lidar_debug.launch.py`)
5. F23 runbook/신호등 latch는 **읽고** 프로토콜·가중치는 무시
6. 깨지면 Kingo FT: `notebooks/kingo_car.ipynb` — 같은 데이터 재학습은 이득 작음
