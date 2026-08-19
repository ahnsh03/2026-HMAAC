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
| 7 | 라이다 장착 | `sensor_bag.launch.py lidar:=true` | OFF | 스캔 방향·보넷 사각 확인 |
| 8 | 신호등 | `main.launch.py` (기본 ON) | 대기 | YOLO 박스 + HSV 색 String |

가중치 스왑은 **스테이지 3에서만** 한다. 제어가 켜진 채로 `.pt`를 바꾸지 말 것.

---

## 1. 지금 `debug_pkg`에 있는 것

엔트리: [`src/debug_pkg/setup.py`](../../src/debug_pkg/setup.py)

| 노드 | 구독 | 발행 | 용도 |
|------|------|------|------|
| `yolov8_visualizer_node` | `/image_raw`, `/detections` | `/yolov8_visualized_img` | 박스·세그 마스크 오버레이. Lifecycle이지만 `main()`이 configure/activate |
| `path_visualizer_node` | `/roi_image`, `/path_planning_result` | `/path_visualized_img` | ROI 위 경로 점 |
| `bev_calibrator_node` | `/detections` | (창) | **트랙바로 IPM `src_mat` 튜닝** |
| `viz_mosaic_node` | `/image_raw`, `/yolov8_visualized_img`, `/lane2_control_bev` | `/race_viz` | 한 창에 camera\|yolo / bev |

`main.launch.py`는 `debug:=true`(기본)일 때 `yolov8_visualizer_node` + `viz_mosaic_node`를 같이 띄운다. **`race_viz` 창 하나**가 주행 중 기본 화면이다. `debug:=false`면 창이 없다.

> 예전에 있던 `control_hud_node` · `lidar_scan_visualizer_node` · `marker_node`는 `race` 브랜치가 `viz_mosaic_node`로 통합하며 정리했다. 특히 `control_hud_node`가 보던 `/control_debug` 토픽은 더 이상 발행되지 않는다(모션 로그 문자열로 흡수). 옛 노드가 필요하면 `backup/pre-race-merge-2026` 태그에 있다.

### 패키지 밖 디버그

| 위치 | 하는 일 | 함정 |
|------|---------|------|
| `lane_info_extractor` `show_image` | edge / BEV / ROI imshow | `src_mat` 기본값이 교육용 하드코딩. 장착각이 다르면 중심 편향 |
| `image_publisher` | `/image_raw` | 코드 기본 `DATA_SOURCE='camera'`, `CAM_NUM=2`. `main.launch.py`는 이 값을 안 덮어쓴다 |
| `data_collection.py` | 손주행·`c`/`v` | ROS bag과 **별개**. 학습 프레임용 |
| lidar 3노드 | `/lidar_raw` → `/lidar_obstacle_info`, `/lidar_lane1_min` | 전용 그림 노드는 없다. `ros2 topic echo /lidar_lane1_min` |

```text
image_raw → yolov8 → detections
                 ├─ yolov8_visualizer
                 ├─ bev_calibrator (트랙바)
                 └─ lane_info_extractor → lane_control_info + lane2_control_bev
                                              └─ motion_planner → serial (main만)

  path_planner_node 는 main.launch.py 에서 띄우지 않는다 (조향은 lane_control_info)
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
| P1 | motion 로그 `ctrl=` 필드 | 명령이 왜 나왔는지 ([controller-tuning](controller-tuning.md) §4) |
| P1 | `dump_roi.py` / `dump_bev.py` | imshow 없이 PNG+행 픽셀 |
| P1 | `topic_rates.sh` · `/finish_stop_reason` | Hz · 정지 사유 |
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
W=$HOME/ros2_ws/weights
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
  model:=$W/teamop_best.pt cam_num:=0

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
# 주의: src0_x… 와 cutting_idx 는 launch 인자가 아니다. 노드 파라미터로 넣는다.
ros2 param set /lane_info_extractor_node src0_x 238
ros2 param set /lane_info_extractor_node src0_y 316
# … src3_y 까지. 영구 반영은 lane_info_extractor_node.py 의 기본값을 고친다.
```

`p` 키가 찍어 주는 줄은 `src0_x:=238 …` 형식이지만 **그대로 launch에 넘길 수는 없다.**
`perception_debug.launch.py`가 받는 인자는 `model` `device` `threshold` `cam_num` `show_image`
다섯 개뿐이다 ([launch-args.md](launch-args.md) §3). 숫자를 옮겨 적는 용도로만 쓴다.

원샷 덤프:

```bash
python3 tools/dump_bev.py /tmp/bev.png
python3 tools/dump_roi.py /tmp/roi.png
```

### 5-5. 세션 로깅 (사후분석)

`main.launch.py`는 `record:=true`가 기본이라 **그냥 띄우면 bag이 같이 돈다.**
따로 폴더·`meta.json`을 남기고 싶을 때만 `run_session.sh`를 쓴다.

```bash
# 터미널 1
ros2 launch launch_pkg main.launch.py record:=false
# 터미널 2
./scripts/run_session.sh     # SESSION 폴더에 bag + meta.json + notes.txt
```

수동 마커 노드는 없어졌다. 랩 구분은 `notes.txt`에 시각을 적거나
`ros2 topic echo /finish_stop_reason`으로 정지 사유를 받는다.

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
  model:=$W/teamop_best.pt drive_speed:=50
```

화면: `race_viz` 창 (`debug:=true` 기본).
토픽: `/topic_control_signal`, `/lane_control_info`, `/finish_stop_reason`.
조향이 왜 그렇게 나왔는지는 `motion_planner_node` 로그의 `ctrl=` 필드를 본다
([controller-tuning.md](controller-tuning.md) §4).

### 5-7. 라이다 (보넷)

```bash
ros2 launch launch_pkg sensor_bag.launch.py lidar:=true processed:=true
ros2 topic echo /lidar_lane1_min      # 전방 최소거리 (정지 판정 입력)
```

`lidar_processor`의 `rotate`/`flip` offset은 그림 보고 맞춘다. 미션 정지는 그 다음.

### 5-8. 신호등

`traffic_light_detector_node`는 `main.launch.py`에서 **항상 켜진다** (끄는 인자 없음).  
박스 = `race_viz`, 색 = `ros2 topic echo /yolov8_traffic_light_info`.  
초록 대기를 건너뛰려면 `require_green_start:=false` 또는 `/force_start` ([wait-green.md](wait-green.md)).

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

`scripts/record_eval_bag.sh`가 넣는 토픽 (실제 배열):
`/image_raw` `/lidar_raw` `/lidar_processed` `/lidar_obstacle_info` `/lidar_lane1_min`
`/detections` `/yolov8_traffic_light_info` `/lane_control_info` `/topic_control_signal`
`/finish_stop_reason`, 그리고 `SKIP_VISUALIZED=1`이 아니면 `/yolov8_visualized_img`
`/lane2_control_bev` `/race_viz`. 떠 있는 토픽만 골라 담는다.

Hz 한 방: `./scripts/topic_rates.sh`

---

## 7. 실패를 어디에 적나

가중치·인지: [yolo-weights.md §4 시트](yolo-weights.md)  
주행·정지: [logging-and-experiments.md](../06-final-eval/logging-and-experiments.md)  
IPM: 세션의 `src_mat.json` + notes에 “코너에서 한쪽으로 쏠림” 등.

다음에 할 일: 가장 나았던 `.pt` + 실패 프레임 → 파인튜닝. 드롭인 1바퀴가 되면 FT는 미룬다.
