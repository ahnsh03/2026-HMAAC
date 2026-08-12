# 로깅 · 실험 준비 (내일)

상태: **가규정(조교 구두, 2026-08-12 · 추가확인 08-13 전)** · 내일 룰미팅 후 확정본으로 갱신  
목적: 정지 FOV 상실·랩 카운트·페널티를 **데이터로** 맞추기. 이 문서는 준비 목록이며, bag 스크립트 코드는 내일 작성한다.  
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
mkdir -p ~/hmaac_logs/$(date +%Y%m%d_%H%M)
cd ~/hmaac_logs/$(date +%Y%m%d_%H%M)

ros2 bag record \
  /image_raw \
  /detections \
  /yolov8_lane_info \
  /yolov8_traffic_light_info \
  /lidar_raw \
  /lidar_processed \
  /lidar_obstacle_info \
  /path_planning_result \
  /topic_control_signal
```

디버그 시각화를 켜면 선택적으로:

```bash
# yolov8_visualizer / path_visualizer 실행 시
# /yolov8_visualized_img  /path_visualized_img
```

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

### 신호등

- [ ] 적→녹 검출 지연(ms/프레임)
- [ ] 오탐: 그림자·플레어·다른 빨간 물체
- [ ] 출발 전 대기 중 조기 출발(a2) 없는지
- [ ] 랩1 중 초록 **유지** 여부
- [ ] **랩2에서 적으로 바뀌는지** (룰미팅·트랙 확인 — 바뀌면 상태머신에 반영)

### 랩 카운트

- [ ] 신호등 **정면 통과**로 랩1/랩2 구분이 되는지 (색 변화로 세지 말 것)
- [ ] 오탐 시 보조 신호(시간·거리) 필요 여부
- [ ] 랩1에 1차로 차량이 **정말 없는지** / 랩2에만 보이는지

### FOV · 정지

- [ ] 1차로 차량 위치: 출발점+약 **30cm** 마킹과 실측 일치
- [ ] 차량이 프레임에서 **사라지는** 거리(줄자)
- [ ] 정지선이 프레임에서 사라지는 거리
- [ ] “보일 때 확정 → LiDAR/지연으로 정지” 파라미터 초안
- [ ] 정지 후 **규정집 위치**(앞바퀴 선 앞·뒷바퀴 선 뒤) 오차 cm
- [ ] LiDAR만 / 카메라만 / 퓨전 — a3/a4 관점 비교

### 차선 · 속도

- [ ] 속도별 점선 침범(b3)·실선 이탈(b1) 빈도
- [ ] 코너 vs 직선 `drive_speed` 분리 필요 여부

## 시도 기록 시트 (복사용)

| 시도 | 시각 | bag/영상 경로 | 랩타임(대략) | 정차오차(cm) | 침범/이탈(회) | 비고 |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

수동 마커 예: `12:05:01 START` / `12:06:10 LAP1` / `12:07:20 LAP2` / `12:07:35 STOP_TRY`

## 내일 착수 순서

1. HW 부팅 · 토픽 hz 확인 ([hw-boot.md](../team/hw-boot.md))
2. `traffic_light` + lidar 노드 launch 주석 해제 후 bag 1회 dry-run
3. 저속 1–2랩으로 **정지 접근 로그** 확보 (출발점+30cm 차량 장면)
4. FOV 상실·**규정집 정지 위치** 오차 측정 → 퓨전 파라미터 초안
5. 정면 통과 랩카운트 검증 · **랩2 적불 여부** 확인 → 상태머신 연결
6. 차선 강건성·속도 튜닝 ([lowspeed-tuning.md](../team/lowspeed-tuning.md))

룰미팅 후: [verbal-briefing.md](verbal-briefing.md)의 상태판을 확정본에 맞춰 이 실험 목록을 수정한다.
