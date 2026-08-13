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
- FOV 상실 대비: 조기 관측 + LiDAR/지연 마무리

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
3. 정지: **차량 감지** 트리거 + 규정집 위치 · 조기 카메라 + 라이다
4. 차선: **좌 점선 밟기 금지** · 우 실선은 밟아도 OK·넘어가면 금지 · 속도–페널티

체크리스트 실행본: [logging-and-experiments.md](logging-and-experiments.md) · [dev-checklist.md](dev-checklist.md)
