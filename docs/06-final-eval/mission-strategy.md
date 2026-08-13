# 미션 개발 전략

상태: **가규정(조교 구두, 2026-08-12 · 추가확인 08-13)** · 확정본 우선  
전제 사실: [verbal-briefing.md](verbal-briefing.md)

## 권장 상태머신

`WAIT_GREEN → LAP1_CRUISE → LAP2_CRUISE → APPROACH_STOP → STOP_HOLD`

| 상태 | 진입 조건 (후보) | 행동 |
|---|---|---|
| `WAIT_GREEN` | 출발선 정렬 · SW 기동 | 신호등 적 유지, **첫** 녹 전이만 출발 (a2 방지) |
| `LAP1_CRUISE` | 초록 확정 | 2차로 추종 · **장애물 없는** 1랩 · **좌 점선 접촉 최소화** |
| `LAP2_CRUISE` | 랩1 완료 이벤트 | 동일 추종 · 1차로 차량 탐색 |
| `APPROACH_STOP` | 랩2 + **차량 감지** | 감속 · 정지 목표 잠금 (신호등 색과 무관) |
| `STOP_HOLD` | 규정집 정지 위치 도달 | 속도 0 · 재출발 금지 |

**신호등:** 랩2 종료까지 **계속 초록**. 주행 중 `red`로 `WAIT_GREEN`에 돌아가면 안 된다. 종료는 **차량 감지**.

## 랩 카운트

**색 변화로 랩을 세지 말 것** (출발 후 초록 고정).

**1차 후보:** 신호등 정면 통과 횟수 · 거리/시간 보조 · 랩2에서 1차로 차량 등장

| 이벤트 | 해석 |
|---|---|
| 대기 | `WAIT_GREEN` |
| 출발 후 첫 정면 재접근 | 랩1 완료 → `LAP2_CRUISE` |
| 두 번째 접근 + **출발선 앞 차량 감지** | `APPROACH_STOP` |

## 정지 전략 (정석: 차량 감지 · 채점: 규정집 위치)

- **트리거:** 랩2 종료 시 출발선 앞 1차로 차량 감지 (신호등 적불 대기 아님)
- **채점 위치:** 앞바퀴=정지선 앞, 뒷바퀴=선 뒤 · a3/a4 규정집
- FOV 상실 대비: 조기 관측 + LiDAR/지연 마무리도 후보

### 팀 논의안 — 단순 정지 휴리스틱 (우선 검토)

정지선 인식·신호등으로 **랩을 세는 방식**보다 단순할 수 있다는 아이디어:

```text
조건 (AND):
  1) 자차 왼쪽(1차로)에 차량이 감지됨
  2) 같은 장면에서 신호등 detection 박스 크기가
     “그 정지 지점”에서 관측되는 대략 N픽셀 근처
     → STOP
```

| 요소 | 역할 |
|---|---|
| 좌측(1차로) 차량 | “랩2 도착 장면이다” / 정지해야 할 구간이라는 **게이트** |
| 신호등 박스 픽셀(폭·높이·면적 중 택1) | 출발선 부근 **거리 프록시** (가까울수록 박스↑) |
| 쓰지 않는 것 | 정지선 세그멘테이션 · 신호등 **색**으로 랩/정지 · 복잡한 랩 카운터 |

왜 단순한가:

- 신호등은 출발선 부근에만 있고 랩2 종료까지 **초록 유지** → 색이 아니라 **박스 크기**만 거리 단서로 씀
- 차량은 1랩에 없고 랩2에만 있음 → 좌측 차량이 보이면 이미 종료 구간일 가능성이 큼
- FOV로 차량이 사라져도, **차량이 보이던 순간 + 신호등 박스≥N**을 동시에 만족하는 구간에서 멈추도록 튜닝 가능

실험으로 잡을 값 (로깅 후 확정):

1. 규정집 정지 위치에 차를 세운 뒤, 그때의 `traffic_light` bbox **width / height / area** 기록 → 임계값 `N` 초안
2. 접근 과정에서 좌측 차량 ON/OFF와 bbox 시계열을 bag으로 확인
3. 오탐: 랩 중간 곡선에서 신호등이 크게 잡히거나, 다른 차량/박스가 좌측으로 잡히는 경우

구현 시 참고 단서:

- YOLO `detections`의 `traffic_light` bbox ([`traffic_light_detector_node`](../../src/camera_perception_pkg/camera_perception_pkg/traffic_light_detector_node.py)가 이미 bbox로 HSV를 침)
- 차량 클래스는 YOLO `detections` 또는 LiDAR 좌전방 섹터
- `motion_planner`에는 **출발용** 적색 `y_max` 로직과 별도로, **종료용** `(left_car && tl_box_size ≥ N)` 분기를 두는 편이 안전

백업: 휴리스틱 실패 시 LiDAR 전방 거리·지연 정지로 폴백한다.

```text
[카메라/라이다] 랩2에서 1차로 차량(출발점+~30cm) 확정
    → stop_needed = true, 목표 파라미터 잠금
[FOV 상실 이후]
    → LiDAR 전방 거리 + 잠근 지연으로 STOP_HOLD
```

## 차선 · 속도 (구두 08-13)

2차로: **왼쪽 점선 / 오른쪽 실선**

| | 밟기 | 넘어감 |
|---|---|---|
| 왼쪽 점선 | **페널티 (b3)** | **페널티 (b1)** |
| 오른쪽 실선 | **무페널티** | **페널티 (b1)** |

- 우선순위: **좌측 점선 클리어런스** > 우측 실선에 살짝 붙는 것
- 우측으로 과도하게 붙이면 OUT 이탈(b1) 위험 — “밟아도 된다”≠“넘어가도 된다”
- 속도–페널티: [lowspeed-tuning.md](../team/lowspeed-tuning.md)

## 레포에서 켤 것

[`src/launch_pkg/launch/main.launch.py`](../../src/launch_pkg/launch/main.launch.py) 기준:

| 노드 | 미션 시 |
|---|---|
| `image_publisher` / `yolov8` / `lane_info_extractor` | 필수 (이미 활성일 수 있음) |
| `traffic_light_detector_node` | **주석 해제** — 출발·랩 카운트 |
| `lidar_publisher` / `processor` / `obstacle_detector` | **주석 해제** — 정지 마무리 |
| `motion_planner` / `path_planner` | 필수 |
| `serial_sender_node` | 실차 필수 (팀 설정에 따라 이미 활성) |

관련 토픽 예: `image_raw`, `detections`, `yolov8_lane_info`, `yolov8_traffic_light_info`, `lidar_raw` / `lidar_processed` / `lidar_obstacle_info`, `path_planning_result`, `topic_control_signal`

## 개발 우선순위 (내일)

1. 로깅 인프라 (bag + 수동 마커)
2. 신호등: 출발 적→녹 · **이후·랩2 종료까지 초록 유지** · 정면 통과 랩카운트(색 변화 X)
3. 정지: **좌측 차량 AND 신호등 박스≈Npx** 휴리스틱 우선 검토 · 규정집 위치 맞춤 · LiDAR 백업
4. 차선: **좌 점선 밟기 금지** · 우 실선은 밟아도 OK·넘어가면 금지 · 속도–페널티

체크리스트 실행본: [logging-and-experiments.md](logging-and-experiments.md) · [dev-checklist.md](dev-checklist.md) · 출발 게이트만: [wait-green.md](../team/wait-green.md)
