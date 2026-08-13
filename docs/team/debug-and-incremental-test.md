# 실차 소단위 디버그 · 시각화 · 로깅

목적: **한 번에 풀 파이프라인을 돌리지 않는다.** 카메라 → 인지 → IPM → (손주행 로그) → 저속 제어 → 라이다 순으로 확인하고, 실패하면 그 단계만 고친다.

관련: [common-commands.md](../common-commands.md) · [yolo-weights.md](yolo-weights.md) · [lowspeed-tuning.md](lowspeed-tuning.md) · [logging-and-experiments.md](../06-final-eval/logging-and-experiments.md) · [repo-structure-and-realcar-guide.md](repo-structure-and-realcar-guide.md)

실차 노트북 경로 `~/ros2_ws` ≈ 이 레포. 스크립트는 레포 루트 `scripts/`, `tools/`.

---

## 0. 내일 한 장 (이 순서)

| # | 스테이지 | launch / 도구 | 모터 | 합격 |
|:-:|----------|---------------|:----:|------|
| 1 | 카메라만 | `camera_only.launch.py` | OFF | `/image_raw` hz, 화면이 트랙 |
| 2 | C920e | `scripts/c920_setup.sh match_train` | OFF | 포커스 고정, 노출/WB auto |
| 3 | 인지 (serial 없음) | `perception_debug.launch.py` | OFF | `lane2` 마스크 + 타겟점 |
| 4 | IPM/BEV | `bev_calibrator_node` 트랙바 | OFF | 차선이 BEV에서 세로로 서고 ROI에 보임 |
| 5 | 손주행 로그 | `data_collection` 또는 perception + `run_session.sh` | 손/OFF | 실패 구간 bag·영상 경로 기록 |
| 6 | 저속 폐루프 | `main.launch.py` + bag | ON 저속 | 이탈 없이 직선→코너 |
| 7 | 라이다 장착 | `lidar_debug.launch.py` | OFF | 스캔 방향·보넷 사각 확인 |
| 8 | 신호등 | `traffic_light_detector` 주석 해제 | 대기 | YOLO 박스 + HSV 색 String |

가중치 스왑은 **스테이지 3에서만** 한다. 제어가 켜진 채로 `.pt`를 바꾸지 말 것.

---

## 1. 지금 `debug_pkg`에 있는 것

엔트리: [`src/debug_pkg/setup.py`](../../src/debug_pkg/setup.py)

| 노드 | 구독 | 발행 | 용도 |
|------|------|------|------|
| `yolov8_visualizer_node` | `/image_raw`, `/detections` | `/yolov8_visualized_img` | 박스·세그 마스크 오버레이. Lifecycle이지만 `main()`이 configure/activate |
| `path_visualizer_node` | `/roi_image`, `/path_planning_result` | `/path_visualized_img` | ROI 위 경로 점 |
| `bev_calibrator_node` | `/detections` | (창) | **트랙바로 IPM `src_mat` 튜닝** |
| `control_hud_node` | image + lane + control | `/control_hud_img` | 조향·속도·타겟을 한 화면에 |
| `lidar_scan_visualizer_node` | `/lidar_raw` (또는 processed) | `/lidar_visualized_img` | 보넷 장착 정렬용 top-down |
| `marker_node` | 키/`/debug_marker_cmd` | `/debug_markers` | START/LAP1/LAP2/STOP_TRY |

`main.launch.py`에는 visualizer가 **없다.** 인지 확인은 `perception_debug.launch.py`를 쓴다.

### 패키지 밖 디버그

| 위치 | 하는 일 | 함정 |
|------|---------|------|
| `lane_info_extractor` `show_image` | edge / BEV / ROI imshow | `src_mat` 기본값이 교육용 하드코딩. 장착각이 다르면 중심 편향 |
| `image_publisher` | `/image_raw` | 코드 기본 `DATA_SOURCE='video'`. 실차는 **launch에서 `data_source:=camera`** |
| `data_collection.py` | 손주행·`c`/`v` | ROS bag과 **별개**. 학습 프레임용 |
| lidar 3노드 | `/lidar_raw` → Bool | 전용 그림은 `lidar_scan_visualizer` |

```text
image_raw → yolov8 → detections
                 ├─ yolov8_visualizer
                 ├─ bev_calibrator (트랙바)
                 └─ lane_info_extractor → roi_image + yolov8_lane_info
                                              ├─ path_planner → path_visualizer
                                              └─ motion → serial (main만)
```

---

## 2. 갭 → 도구 (우선순위)

이미 있던 것: 파이프라인 노드, YOLO/path visualizer 코드, lane imshow, data_collection, 문서상 bag 스케치.

| P | 도구 | 왜 |
|:-:|------|-----|
| P0 | `camera_only` / `perception_debug` launch | serial 없이 인지만 |
| P0 | `c920_setup.sh` | 포커스 잠금, 학습 분포(`match_train`) |
| P0 | `bev_calibrator` 트랙바 | 장착각 ≠ 하드코딩 IPM |
| P0 | `run_session.sh` + bag | 사후분석 |
| P1 | `control_hud` · `control_debug` | 명령이 왜 나왔는지 |
| P1 | `lidar_scan_visualizer` | 보넷 위 장착 방향 |
| P1 | `dump_roi.py` / `dump_bev.py` | imshow 없이 PNG+행 픽셀 |
| P1 | `marker_node` · `topic_rates.sh` | 랩 시각 · Hz |
| P2 | TL HSV 디버그 이미지 | **Plan B** — 색 오판 때만 |

시뮬에서 이식: `dump_roi`/`dump_bev`/`topic_rates`. Gazebo GT(`lap_monitor`, `lane_gt`)는 **이식하지 않음**.

---

## 3. C920e — auto vs 고정

기종: Logitech **C920e** (Kingo/TeamOP 계열도 동일 기종일 가능성 큼).

로비: 실내등 상시 + 창문·반투명 필름. 햇빛은 **느리게** 변함. 야외처럼 급격한 대비는 적음.

### 권장: `match_train` (기본)

웹 가중치는 대체로 **카메라 기본(AE/AWB auto)** 로 찍었을 가능성이 크다. 노출·WB를 우리가 세게 고정하면 **학습 분포만 멀어진다.**

| 제어 | `match_train` | `full_lock` |
|------|---------------|-------------|
| `focus_auto` | **OFF** (헌팅이 인식에 최악) | OFF |
| `focus_absolute` | 트랙이 선명해질 때까지 | 동일 |
| `exposure_auto` | **3** Aperture Priority | **1** Manual |
| `exposure_absolute` | (auto가 잡음) | 트랙 중앙에서 샘플 |
| WB auto | **ON** | OFF + temperature 고정 |
| brightness/contrast | 기본(128) 유지 | 기본 유지 |

```bash
# 장치 확인 (짝수 노드가 영상인 경우가 많음)
v4l2-ctl --list-devices
ls -l /dev/video*

# 포커스만 잠그고 AE/AWB는 auto
./scripts/c920_setup.sh match_train /dev/video0

# AE hunting이 심하거나 FT용 수집일 때만
./scripts/c920_setup.sh full_lock /dev/video0
```

**전부 픽스하는 게 낫지 않다.** 동일 C920e면 포커스 잠금 + auto 노출/WB가 드롭인 가중치와 가장 가깝다.

| 상황 | 선택 |
|------|------|
| 드롭인 테스트·평가 주행 | `match_train` |
| 창을 향해 돌 때 밝기가 펌핑 | 트랙 중앙에서 `full_lock` |
| 파인튜닝용 프레임 수집 | `full_lock` (분포 안정) |
| 밝기/대비를 크게 올리기 | 하지 말 것 |

고정 가능한 대표 컨트롤: brightness, contrast, saturation, sharpness, gain, white_balance_temperature(+auto), exposure_auto / exposure_absolute, focus_auto / focus_absolute, backlight_compensation, `power_line_frequency=2`(60Hz).

YOLO와의 관계: 카메라 튜닝은 과다/과소·블러를 줄이는 **보조**. 도메인 갭(각도·커튼)은 가중치 스왑·FT가 1순위.

---

## 4. 신호등 — YOLO 박스 + HSV 색 (Plan A / B)

색을 YOLO 클래스로 나누지 않는다.

```text
yolov8  →  class_name == "traffic_light" (박스)
              ↓
traffic_light_detector_node  →  박스 ROI에 HSV → Red/Yellow/Green/Unknown
              ↓
/yolov8_traffic_light_info
```

| | Plan A (내일) | Plan B |
|--|----------------|--------|
| 박스 | `yolov8_visualizer` + `/detections` | 동일 |
| 색 | HSV 노드 launch 주석 해제 ([13일 튜닝](tl-hsv-tuning.md)) | HSV 마스크 오버레이 노드 (미구현, 조명 바뀌어 오판 시) |
| 언제 | 초록 출발 미션 | 조명·WB가 13일과 달라 **게이트를 다시 잴 때** |

HSV 디버그 이미지는 **필수 산출물이 아니다.**

---

## 5. 스테이지별 명령

공통:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export ROS_LOCALHOST_ONLY=1
cd ~/ros2_ws
W=$HOME/ros2_ws/src/camera_perception_pkg/camera_perception_pkg/weights
```

### 5-1. 카메라만

```bash
ros2 launch launch_pkg camera_only.launch.py cam_num:=0
# 다른 터미널
ros2 topic hz /image_raw
```

화면이 노트북 웹캠이면 `cam_num`을 `ls /dev/video*`의 **외장 짝수**로.

### 5-2. C920e

```bash
./scripts/c920_setup.sh list /dev/video0
./scripts/c920_setup.sh match_train /dev/video0
```

USB를 뽑았다 꽂으면 다시 실행.

### 5-3. 인지 (모터 없음)

```bash
ros2 launch launch_pkg perception_debug.launch.py \
  model:=$W/teamop_best.pt device:=cuda:0 cam_num:=0

ros2 topic echo /detections --once
ros2 topic echo /yolov8_lane_info --once
# 창: yolov8_visualized_img, lane imshow (edge/BEV/ROI)
```

통과: `lane2` 마스크 + 타겟점. 실패 시 [yolo-weights.md §3](yolo-weights.md) (`teamop` 기본, 차선만 `best_psh`)로 `.pt`만 교체하고 **시트에 실패 지점 기록**. IPM은 `.pt`마다 다시 맞추지 말 것.

### 5-4. IPM 트랙바

인지 launch가 뜬 상태에서:

```bash
ros2 run debug_pkg bev_calibrator_node
```

트랙바: 사다리꼴 4점(`src0`…`src3`) + `cutting_idx`.  
차선이 BEV에서 **세로로** 서고, 아래 ROI에 양쪽(또는 중심)이 보이게.

- `p` : launch/param 문자열 출력
- `s` : `src_mat.json` 저장 (cwd 또는 `HMAAC_SESSION`)

반영:

```bash
ros2 launch launch_pkg perception_debug.launch.py \
  model:=$W/teamop_best.pt device:=cuda:0 \
  src0_x:=238 src0_y:=316 src1_x:=402 src1_y:=313 \
  src2_x:=501 src2_y:=476 src3_x:=155 src3_y:=476 \
  cutting_idx:=300
```

원샷 덤프:

```bash
python3 tools/dump_bev.py /tmp/bev.png
python3 tools/dump_roi.py /tmp/roi.png
```

### 5-5. 세션 로깅 (사후분석)

```bash
./scripts/run_session.sh
# 안내된 SESSION 폴더에 bag + meta.json
# 다른 터미널에서 launch (perception 또는 main)
```

마커 (창이 포커스일 때): `s` START · `1` LAP1 · `2` LAP2 · `t` STOP_TRY  
또는 `ros2 topic pub --once /debug_marker_cmd std_msgs/String "data: START"`

재생:

```bash
ros2 bag play ~/hmaac_logs/<TS>/bag
```

큰 bag은 레포에 커밋하지 않는다. 시트에 **경로만**.

### 5-6. 저속 폐루프

인지·IPM이 합격한 뒤에만.

```bash
./scripts/run_session.sh
ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt device:=cuda:0 \
  data_source:=camera cam_num:=0 drive_speed:=50
```

HUD: `ros2 run debug_pkg control_hud_node`  
토픽: `/topic_control_signal`, `/control_debug`

### 5-7. 라이다 (보넷)

```bash
ros2 launch launch_pkg lidar_debug.launch.py
# OpenCV top-down: 전방이 위쪽인지, 차체가 가리는 부채꼴이 어디인지
```

`lidar_processor`의 `rotate`/`flip` offset은 그림 보고 맞춘다. 미션 정지는 그 다음.

### 5-8. 신호등

`main.launch.py`에서 `traffic_light_detector_node` 주석 해제.  
박스 = visualizer, 색 = `ros2 topic echo /yolov8_traffic_light_info`.

---

## 6. 로깅 폴더 규약

```text
~/hmaac_logs/YYYYMMDD_HHMMSS/
  bag/          # ros2 bag
  meta.json     # 가중치, drive_speed, c920 profile, git sha
  notes.txt
  markers.csv
  src_mat.json  # 캘리브 시
```

`scripts/record_eval_bag.sh`가 넣는 토픽: `image_raw`, `detections`, `yolov8_lane_info`, `path_planning_result`, `topic_control_signal`, (있으면) TL/lidar/visualized/control_debug/debug_markers.

Hz 한 방: `./scripts/topic_rates.sh`

---

## 7. 실패를 어디에 적나

가중치·인지: [yolo-weights.md §4 시트](yolo-weights.md)  
주행·정지: [logging-and-experiments.md](../06-final-eval/logging-and-experiments.md)  
IPM: 세션의 `src_mat.json` + notes에 “코너에서 한쪽으로 쏠림” 등.

다음에 할 일: 가장 나았던 `.pt` + 실패 프레임 → 파인튜닝. 드롭인 1바퀴가 되면 FT는 미룬다.
