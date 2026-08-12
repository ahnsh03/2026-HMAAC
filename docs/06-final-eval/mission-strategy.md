# 미션 개발 전략

상태: **가규정(조교 구두, 2026-08-12 · 추가확인 08-13 전)** · 내일 룰미팅 후 확정본으로 갱신  
전제 사실: [verbal-briefing.md](verbal-briefing.md)

## 권장 상태머신

`WAIT_GREEN → LAP1_CRUISE → LAP2_CRUISE → APPROACH_STOP → STOP_HOLD`

| 상태 | 진입 조건 (후보) | 행동 |
|---|---|---|
| `WAIT_GREEN` | 출발선 정렬 · SW 기동 | 신호등 적 유지, **첫** 녹 전이만 출발 (a2 방지) |
| `LAP1_CRUISE` | 초록 확정 | 2차로 추종 · **장애물 없는** 1랩 |
| `LAP2_CRUISE` | 랩1 완료 이벤트 | 동일 추종 · 1차로 차량/정지 장면 탐색 |
| `APPROACH_STOP` | 랩2 + 물체/장면 단서 | 감속 · 정지 목표 잠금 |
| `STOP_HOLD` | 규정집 정지 위치 도달 | 속도 0 · 재출발 금지 |

**주의:** 랩 중 신호등은 보통 **초록 유지**. 랩2에서 적으로 바뀔 **가능성**이 있으므로, 주행 중 `red`를 `WAIT_GREEN`으로 되돌리면 안 된다. (`started==true` 이후 적 무시 또는 별도 정책 — 내일 확인 후 고정)

## 랩 카운트

**색 변화로 랩을 세지 말 것** (출발 후 초록 고정이 기본).

**1차 후보:** 신호등 **정면(통과/근접) 횟수** 또는 거리·시간 보조

| 이벤트 | 해석 |
|---|---|
| 대기 | `WAIT_GREEN` |
| 출발 후 첫 정면 재접근 | 랩1 완료 → `LAP2_CRUISE` |
| 두 번째 정면 재접근 + 1차로 차량 | 랩2 → `APPROACH_STOP` |

보조:

- 휠 명령 적분(거친 거리) · 코스 특징점
- “1차로 차량이 보이기 시작” = **랩2 전용** (출발점+약 30cm 앞 · 1대). 랩1에는 없음

검증: [logging-and-experiments.md](logging-and-experiments.md)

## 정지 전략 (정석: 물체 탐지 · 채점: 규정집 위치)

- **정석 트리거:** 1차로 정차 차량(물체) 탐지 후 정지
- **채점 위치:** 앞바퀴=정지선 앞, 뒷바퀴=선 뒤 ([operations.md](operations.md)). a3/a4는 규정집
- 수단은 자유이나 FOV 상실 대비 **조기 관측 + 지연 마무리**는 유지

```text
[카메라/라이다] 랩2에서 1차로 차량(출발점+~30cm) 확정
    → stop_needed = true, 목표 파라미터 잠금
[FOV 상실 이후]
    → LiDAR 전방 거리 + 잠근 지연으로 STOP_HOLD
    → 최종 자세는 규정집 정지선(앞·뒤 바퀴)에 맞출 것
```

| 레이어 | 역할 |
|---|---|
| 카메라 YOLO | 랩2 물체·장면 조기 확정 |
| 카메라 정지선 | 보일 때 보정 · 최종에선 FOV 밖일 수 있음 |
| 2D LiDAR | 물체 거리로 마무리 (정석에 가까움) |
| 시간/명령 적분 | 백업 |

파라미터는 트랙에서 **줄자(30cm 오프셋·정지선)** 로 맞춘다.

## 차선 · 속도

- 목표: **2차로 유지** · IN 점선 침범(b3)·OUT 실선 이탈(b1) 최소화
- 페널티가 전부 시간이므로, 무리한 고속보다 **침범 0회 + 합리적 속도**가 유리한 경우가 많음
- 직선/코너별 `drive_speed` 실험은 [lowspeed-tuning.md](../team/lowspeed-tuning.md)와 연계

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
2. 신호등: 출발 적→녹 · **랩2 적 전환 여부** 확인 · 정면 통과 랩카운트(색 변화 X)
3. 정지 퓨전 (물체 탐지 정석 + 규정집 위치 · 조기 카메라 + 라이다)
4. 차선 강건성 · 속도–페널티 트레이드오프

체크리스트 실행본: [logging-and-experiments.md](logging-and-experiments.md) · [dev-checklist.md](dev-checklist.md)
