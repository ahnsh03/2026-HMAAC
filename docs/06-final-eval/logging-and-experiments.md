# 로깅 · 실험 준비 (내일)

상태: **가규정(조교 구두, 2026-08-12 · 추가확인 08-13 전)** · 내일 룰미팅 후 확정본으로 갱신  
목적: 정지 FOV 상실·랩 카운트·페널티를 **데이터로** 맞추기.  
스크립트: [`scripts/run_session.sh`](../../scripts/run_session.sh) · [`scripts/record_eval_bag.sh`](../../scripts/record_eval_bag.sh) · [`scripts/topic_rates.sh`](../../scripts/topic_rates.sh)  
스테이지·HUD·마커: [team/debug-and-incremental-test.md](../team/debug-and-incremental-test.md)  
채점 정지 위치는 **규정집**(앞·뒤 바퀴 vs 정지선). 도착 차량 ≈ 출발점+**30cm** · 1차로 1대 · 1랩에는 없음.

관련: [verbal-briefing.md](verbal-briefing.md) · [mission-strategy.md](mission-strategy.md)

## 저장 경로 관례

큰 bag/영상은 레포에 커밋하지 않는다.

```text
# 예 (gitignore 대상인 Collected_Datasets 하위 또는 홈)
~/ros2_ws/src/camera_perception_pkg/.../Collected_Datasets/eval_logs/YYYYMMDD_HHMM/
# 또는
~/hmaac_logs/YYYYMMDD_HHMM/
```

시도마다 폴더를 나누고, 아래 기록 시트에 **경로**를 남긴다.

## 로깅 우선순위

1. **ROS bag** — 인지·제어 동기 재생
2. **수동 마커** — 출발 / 랩1 / 랩2 / 정지시도 시각 (터미널 메모 또는 키 입력 시각)
3. **정지 구간 집중** — 접근 전후 10–20초 카메라·라이다·명령
4. (보조) `data_collection.py`의 `v` 녹화로 접근 구간 영상

### bag에 넣을 토픽 (스케치)

실제 토픽명은 `ros2 topic list`로 확인 후 조정.

```bash
# 워크스페이스 source 후
./scripts/run_session.sh
# 다른 터미널에서 launch. 폴더: ~/hmaac_logs/YYYYMMDD_HHMMSS/
```

수동으로 토픽만 고를 때:

```bash
./scripts/record_eval_bag.sh ~/hmaac_logs/manual/bag
```

디버그 시각화는 `perception_debug` / `debug_overlay` 가 `/yolov8_visualized_img` `/path_visualized_img` `/control_hud_img` 를 켠다. bag 스크립트가 **떠 있는 토픽만** 고른다.

### 센서 생존 확인

```bash
ros2 topic hz /image_raw
ros2 topic hz /lidar_raw
ros2 topic echo /yolov8_traffic_light_info
ros2 topic echo /lidar_obstacle_info
ros2 topic echo /topic_control_signal
```

### 영상만 빠르게

```bash
python3 src/data_collection/data_collection.py
# 프리뷰 포커스 후 v = 녹화 토글 · 정지 접근 구간만 짧게
```

## 실험 체크리스트

### YOLO 가중치 스왑 (인지 실패)

드롭인 테스트·실패 기록·파인튜닝 정의: **[team/yolo-weights.md §4](../team/yolo-weights.md)**  
한 줄: 여러 `.pt` 비교 → **실패 지점 기록** → 최우수 가중치 + 실패 장면 로깅·라벨 → FT.

- [ ] 가중치별 정지 `lane2` / 타겟점 / 신호
- [ ] 깨지는 구간·증상(끊김·편향 등) 시트에 남김
- [ ] 실패 구간 bag 또는 `data_collection` `v` 경로 기록

### 신호등

- [ ] 적→녹 검출 지연(ms/프레임)
- [ ] 오탐: 그림자·플레어·다른 빨간 물체
- [ ] 출발 전 대기 중 조기 출발(a2) 없는지
- [ ] 랩1 중·**랩2 종료까지** 초록 **유지** 확인 (종료 트리거≠적불)
- [ ] 출발 전 조기 출발(a2) 없는지

### 랩 카운트

- [ ] 신호등 **정면 통과**로 랩1/랩2 구분 (색 변화로 세지 말 것)
- [ ] 랩1에 1차로 차량 없음 / 랩2에만 보이는지

### FOV · 정지

- [ ] 출발선 앞 차량 **감지 → 정지** 트리거 동작
- [ ] 차량 위치: 출발점+약 **30cm** 실측
- [ ] **단순 휴리스틱:** 좌측 차량 ON일 때, 규정집 정지 위치에서의 신호등 bbox width/height/area → 임계 `N` 기록
- [ ] 접근 중 bbox 시계열 + 좌측 차량 플래그를 bag으로 확인 (랩 중간 오탐 여부)
- [ ] FOV 상실 거리 · 규정집 정지 위치 오차 cm
- [ ] LiDAR만 / 카메라만 / **차량+TL박스** / 퓨전 — a3/a4

### 차선 · 속도

- [ ] **왼쪽 점선** 접촉(b3) 빈도 — 최우선 감소
- [ ] 오른쪽 실선: 밟아도 OK인지 확인 · **넘어감(b1)** 발생 여부
- [ ] 속도별 침범/이탈 트레이드오프
- [ ] 코너 vs 직선 `drive_speed` 분리 필요 여부

## 시도 기록 시트 (복사용)

| 시도 | 시각 | bag/영상 경로 | 랩타임(대략) | 정차오차(cm) | 침범/이탈(회) | 비고 |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

수동 마커: `ros2 run debug_pkg marker_node` (s/1/2/t) 또는 `ros2 topic pub --once /debug_marker_cmd std_msgs/String "data: START"`  
시트 예: `12:05:01 START` / `12:06:10 LAP1` / `12:07:20 LAP2` / `12:07:35 STOP_TRY`

## 내일 착수 순서

1. HW 부팅 · 토픽 hz 확인 ([hw-boot.md](../team/hw-boot.md)) · 소단위 스테이지 ([debug-and-incremental-test](../team/debug-and-incremental-test.md))
2. `./scripts/run_session.sh` dry-run (perception 또는 main). 신호등·라이다는 켠 뒤에 토픽이 bag에 자동 포함.
3. 저속 1–2랩으로 **정지 접근 로그** 확보 (출발점+30cm 차량 장면)
4. FOV 상실·**규정집 정지 위치** 오차 측정 → 퓨전 파라미터 초안
5. 정면 통과 랩카운트 · **차량 감지 정지** → 상태머신
6. 차선: 좌 점선 클리어런스 우선 · [lowspeed-tuning.md](../team/lowspeed-tuning.md)

룰미팅 후: [verbal-briefing.md](verbal-briefing.md)의 상태판을 확정본에 맞춰 이 실험 목록을 수정한다.
