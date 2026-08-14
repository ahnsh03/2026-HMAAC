# Launch 인자 — `이름:=값`으로 넘기는 변수

기준: `race` 작업트리, 2026-08-14.  
소스: [`ros2_ws/src/launch_pkg/launch/`](../../../ros2_ws/src/launch_pkg/launch/).  
실행 예: [cheat-sheet.md](cheat-sheet.md) · 제어 숫자 의미: [controller-tuning.md](controller-tuning.md)

```bash
source /opt/ros/humble/setup.bash
source ~/team14/ros2_ws/install/setup.bash
ros2 launch launch_pkg main.launch.py steer_k:=0.044 drive_speed:=250
```

마지막에 적은 같은 이름이 이긴다. `true`/`false`는 소문자.

---

## 1. `main.launch.py` (주행)

17개. 선언만 하고 노드에 안 넘기는 것은 없다.

### 주행·조향

코드 기본: [`motion_planner_node.py`](../../../ros2_ws/src/decision_making_pkg/decision_making_pkg/motion_planner_node.py)  
launch 전달: [`main.launch.py`](../../../ros2_ws/src/launch_pkg/launch/main.launch.py)

| 인자 | 기본 | 파일 | 의미 |
|---|---|---|---|
| `drive_speed` | `250` | motion + main | 차로 추종 좌우 PWM |
| `steer_k` | `0.044` | motion + main | BEV 중심 P 게인 [조향스텝/픽셀] |
| `steer_max` | `7` | motion + main | 조향 절댓값 상한 |
| `steer_alpha` | `1.0` | motion + main | EMA. `1`이면 필터 꺼짐 |
| `steer_rate` | `7.0` | motion + main | 0.1초당 조향 변화 상한. `7`이면 slew 꺼짐 |
| `require_green_start` | `true` | motion + main | 초록 3틱(또는 `/force_start`) 전에 대기. 구간 테스트는 `false` |
| `vehicle_center_x` | `320.0` | motion + main | P 조향 목표 x. bag 평가 기준 320 |

조향 게인(`steer_k` 등)은 실행 중에도 바로 먹는다.

### 인지 (BEV)

코드 기본: [`lane_info_extractor_node.py`](../../../ros2_ws/src/camera_perception_pkg/camera_perception_pkg/lane_info_extractor_node.py) (`model`은 [`yolov8_node`](../../../ros2_ws/src/camera_perception_pkg/camera_perception_pkg/yolov8_node.py))  
launch 전달: [`main.launch.py`](../../../ros2_ws/src/launch_pkg/launch/main.launch.py)

| 인자 | 기본 | 파일 | 의미 |
|---|---|---|---|
| `model` | `ros2_ws/best.pt` | yolov8 + main | YOLO 가중치 절대 경로. 재런치 필요 |
| `control_cutting_idx` | `160` | extractor + main | BEV 위에서 버릴 행 수. `0`이면 전체 |
| `control_min_area` | `1000.0` | extractor + main | 이보다 작은 마스크는 중심 무효(nan) |
| `center_mode` | `moments` | extractor + main | `moments`면 블렌드, `row_mid`면 하단 행중점만 |
| `row_mid_power` | `2.0` | extractor + main | 가까운 점 가중 `(y+1)^p` |
| `near_blend` | `1.0` | extractor + main | β. `0`이면 모멘트만(예전), `1`이면 가깝게만 |

bag 스윕 승자: `cut=160`, `p=2`, `β=1`. `center_mode:=moments near_blend:=0`이면 예전과 같다. 위 인자는 매 프레임 읽는다.

```bash
ros2 launch launch_pkg main.launch.py center_mode:=moments near_blend:=0
ros2 param set /lane_info_extractor_node near_blend 0.75
ros2 param set /motion_planner_node vehicle_center_x 320
```

### 창·기록

| 인자 | 기본 | 의미 |
|---|---|---|
| `debug` | `true` | `race_viz` 한 창 (위 camera\|yolo, 아래 bev). `false`면 창 없음 |
| `record` | `true` | eval bag 기록. Ctrl+C로 닫힘 |
| `bag_dir` | 빈 값 | bag 부모 폴더. 비우면 `ros2_ws/bags` |
| `skip_visualized` | `false` | bag에서 오버레이 영상 제외 |

### 자주 쓰는 줄

```bash
ros2 launch launch_pkg main.launch.py
ros2 launch launch_pkg main.launch.py require_green_start:=false drive_speed:=50
ros2 launch launch_pkg main.launch.py skip_visualized:=true
ros2 launch launch_pkg main.launch.py record:=false
ros2 launch launch_pkg main.launch.py debug:=false
```

구간 테스트 출발: [wait-green.md](wait-green.md)

```bash
ros2 topic pub --once /force_start std_msgs/msg/Bool "{data: true}"
```

---

## 2. `main.launch`로 안 들어가는 것

노드에는 있지만 launch 인자가 없다. 코드 기본값을 쓴다.

| 파라미터 | 기본 | 노드 |
|---|---|---|
| `lane_timeout` | `0.35` | motion. 이보다 오래 중심이 없으면 `lane_lost` |
| `lane_lost_speed` | `30` | motion |
| `lidar_stop_rmin` / `lidar_stop_rmax` | `0.12` / `0.95` | motion |
| `enable_finish_stop` | `true` | motion |
| `need_green_hits` | `3` | motion. 시작 때 한 번 |
| `cam_num` | `2` (`/dev/video2`) | image_publisher |
| `src0_x` … `src3_y` | 교육 기본 IPM | extractor. 시작 때 한 번 |

카메라 번호·IPM은 아래 소단위 launch로 넘긴다.

---

## 3. 소단위 launch

### `camera_only.launch.py`

| 인자 | 기본 | 의미 |
|---|---|---|
| `cam_num` | `0` | `/dev/videoN` |

### `bev_calibrate.launch.py`

| 인자 | 기본 | 의미 |
|---|---|---|
| `cam_num` | `0` | `/dev/videoN` |

창에서 사다리꼴을 맞추고 `p`로 숫자를 복사한다.

### `perception_debug.launch.py`

serial/motion 없음. 인지 A/B용.

| 인자 | 기본 | 의미 |
|---|---|---|
| `model` | `ros2_ws/best.pt` | YOLO 가중치 |
| `device` | `cuda:0` | 추론 장치 |
| `threshold` | `0.5` | YOLO 점수 임계 |
| `cam_num` | `0` | `/dev/videoN` |
| `show_image` | `true` | `race_viz` 창 |
| `src0_x` `src0_y` `src1_x` `src1_y` `src2_x` `src2_y` `src3_x` `src3_y` | 238,316 / 402,313 / 501,476 / 155,476 | IPM 사다리꼴 |
| `cutting_idx` | `300` | 예전 ROI. P 제어는 안 봄. 인자는 받음 |

```bash
W=$HOME/ros2_ws/weights
SRC='src0_x:=238 src0_y:=316 src1_x:=402 src1_y:=313 src2_x:=501 src2_y:=476 src3_x:=155 src3_y:=476'
ros2 launch launch_pkg perception_debug.launch.py model:=$W/teamop_best.pt device:=cuda:0 cam_num:=0 $SRC
```

### `sensor_bag.launch.py`

센서만 켜고 bag. 시리얼·모션 없음.

| 인자 | 기본 | 의미 |
|---|---|---|
| `cam_num` | `2` | C920은 보통 2 |
| `show_image` | `true` | 카메라 미리보기 |
| `lidar` | `true` | `/lidar_raw` 기록 |
| `processed` | `false` | processor/obstacle도 기록 |
| `bag_dir` | 빈 값 | 기본 `ros2_ws/bags` |

---

## 4. 재시작이 필요한 것

| 바꾸는 방법 | 바로 먹음 | launch 다시 띄움 |
|---|---|---|
| `ros2 param set /motion_planner_node steer_*` | 예 | — |
| `ros2 param set /motion_planner_node drive_speed` | 예 | — |
| `ros2 param set /lane_info_extractor_node control_cutting_idx` | 예 | — |
| `ros2 param set /lane_info_extractor_node control_min_area` | 예 | — |
| `ros2 param set /lane_info_extractor_node center_mode` | 예 | — |
| `ros2 param set /lane_info_extractor_node row_mid_power` | 예 | — |
| `ros2 param set /lane_info_extractor_node near_blend` | 예 | — |
| `ros2 param set /motion_planner_node vehicle_center_x` | 예 | — |
| `src_*` | 아니오 | 예 |
| `cam_num` / `model` | 아니오 | 예 |
