# 제어기 튜닝 — 지금 도는 코드와 남은 노브

기준: `main` (구 `2026` + `race` 병합본), 2026-08-19 재작성.
소스: [`motion_planner_node.py`](../../src/decision_making_pkg/decision_making_pkg/motion_planner_node.py) · 인자: [launch-args.md](launch-args.md)
인지 비교: [teamop-vs-team14.md](teamop-vs-team14.md) · 초록 출발: [wait-green.md](wait-green.md)

주행 기본 가중치는 **`teamop_best.pt`** (자동 선택). `best_psh`는 차선만 A/B용, `best_psh_v2`는 차선이 없어 쓰지 않는다 — [`weights/README.md`](../../weights/README.md)

> 이 문서는 2026-08-13 판에서 **bang-bang 기준으로 쓰여 있었다.** `race` 브랜치가 8/13~14에 조향 파이프라인을 통째로 갈아서, 그때의 P0/P1 노브 대부분이 이미 코드에 들어갔다. (그 브랜치는 `main`에 병합 후 `race-final-2026-08-14` 태그로 박제하고 삭제했다.) 아래는 **지금 도는 코드** 기준이다. 옛 계획 대비 무엇이 반영됐는지는 §5.

---

## 1. 지금 도는 파이프라인

```text
lane2 마스크
  → extractor  BEV 채운 차선면 → 중심 x 한 개 (moments ↔ row_mid 블렌드)
               control_cutting_idx=160 위쪽 잘라냄 · control_min_area=1000 미만은 무효(nan)
  → lane_control_info  (center_x, area, stamp)
  → motion_planner  P 제어
  → serial  s{steer}l{L}r{R}\n
```

**`path_planner_node`(CubicSpline)는 `main.launch.py`에서 더 이상 띄우지 않는다.** 조향은 스플라인 경로가 아니라 BEV 차선면 중심 하나로 계산한다. 노드 파일과 `PathPlanningResult.msg`는 남아 있지만 주행 경로에서 빠져 있다.

### 조향 계산 ([`_follow_lane_surface`](../../src/decision_making_pkg/decision_making_pkg/motion_planner_node.py))

```python
error_px = center_x - vehicle_center_x          # 320.0
raw      = clamp(steer_k * error_px, ±steer_max) # 0.044, ±7
filtered = (1-α)*filtered + α*raw                # α = steer_alpha = 1.0 → 필터 통과
delta    = clamp(filtered - limited, ±steer_rate) # 7.0
limited  = clamp(limited + delta, ±steer_max)
steering = int(round(limited))
```

| 상수 | 값 | 의미 |
|---|---|---|
| `steer_k` | `0.044` | 조향스텝/픽셀. 오차 160px에서 포화(0.044×160 ≈ 7) |
| `vehicle_center_x` | `320.0` | BEV 목표 x. bag 평가 기준 |
| `steer_max` | `7` | ino `MAX_STEERING_STEP`과 일치. 8을 보내도 보드가 자른다 |
| `steer_alpha` | `1.0` | **EMA 꺼짐.** 낮추면 반응이 느려지고 부드러워진다 |
| `steer_rate` | `7.0` | 한 틱(0.1s) 변화 상한. 조향 폭이 −7~+7(14칸)이라 전체 반전은 2틱 |

### 속도 분기 ([`_follow_path`](../../src/decision_making_pkg/decision_making_pkg/motion_planner_node.py))

| 상태 | 조건 | 조향 | 속도 |
|---|---|---|---|
| `ctrl=wait_lane` | 유효 center가 **한 번도** 안 옴 | 0 | **0** (정지) |
| `ctrl=surface` | center 나이 ≤ `lane_timeout` 0.35s | P 제어 | `drive_speed` **250** |
| `ctrl=lane_lost` | center가 0.35s 넘게 없음 | **0으로 리셋** | `lane_lost_speed` **30** |

옛 문서의 "경로 없으면 조향 0 + 속도 유지 → 직진으로 들이받는다"는 **해결됐다.** 지금은 차선을 놓치면 30까지 떨어지고, 시작 전에는 아예 안 나간다.

### 출발·정지

| 항목 | 값 | 동작 |
|---|---|---|
| `require_green_start` | `true` | 초록 `need_green_hits`=3틱 연속 → 출발 |
| `green_start_timeout` | `15.0` | 초록을 못 봐도 15초 뒤 자동 출발. `0`이면 무한 대기 |
| `/force_start` | — | `std_msgs/Bool true` 발행하면 즉시 출발 |
| `enable_finish_stop` | `true` | 2랩 정지 |
| `lidar_stop_rmin/rmax` | `0.12` / `0.95` | `lidar_lane1_min`이 이 구간이면 정지 후보 |
| `need_finish_hits` | `3` | 3틱 연속이어야 정지 확정 |

정지는 **라이다 거리만** 본다. 신호등 박스가 보이는지는 조건이 아니다 (`_finish_source`).

---

## 2. 인지와 제어를 분리한다

한 번에 가중치와 조향을 같이 바꾸지 않는다. 고정할 것: 속도, 조향 상수, BEV, 카메라, threshold. 바꿀 것: `model:=` 만.

```bash
W=~/ros2_ws/weights

# 1) 주행 기본 (차선+신호등)
ros2 launch launch_pkg main.launch.py

# 2) 차선만 A/B (신호등 약함)
ros2 launch launch_pkg main.launch.py model:=$W/best_psh.pt
```

같은 코스(직선 → 첫 코너 → S자)를 두 번. 기록은 §6 시트.

| 결과 | 의미 | 다음 |
|---|---|---|
| 둘 다 같은 곳에서 이탈 | **제어** | §3 노브 |
| psh만 통과, teamop만 이탈 | **마스크 품질** | 그 구간은 인지. 제어는 psh로 진행 |
| 둘 다 직선 OK, 코너만 흔들림 | 게인 과대 또는 속도 | `steer_k`↓ 또는 `drive_speed`↓ |
| 한쪽으로만 붙음 | BEV·목표 x 편향 | `vehicle_center_x` 재측정, `bev_calibrator` |

team14는 이 A/B에 넣지 않는다 ([teamop-vs-team14.md](teamop-vs-team14.md)).

---

## 3. 남은 노브 (효과 / 위험)

전부 `ros2 param set`으로 **주행 중에 바로 먹는다.** 한 번에 하나만.

| 순위 | 노브 | 언제 | 시작값 | 위험 |
|:---:|---|---|---|---|
| 1 | `drive_speed`↓ | 코너 이탈·전반적 불안정 | 250 → 180 → 120 | 느리면 랩타임 손해 |
| 2 | `steer_k`↓ | 직선에서 좌우로 흔들림(과대 게인) | 0.044 → 0.035 | 코너 진입이 늦어짐 |
| 3 | `steer_alpha`↓ | 채터가 남을 때 EMA를 켠다 | 1.0 → 0.6 → 0.4 | 반응 지연. 코너에서 밖으로 |
| 4 | `steer_rate`↓ | 한 틱 급변을 막는다 | 7.0 → 3.0 → 2.0 | 코너가 무뎌짐 |
| 5 | `vehicle_center_x` | 한쪽으로 일정하게 붙음 | 320 ± 실측 오프셋 | 남의 숫자 복붙 금지 |
| 6 | `near_blend` | 중심이 멀리를 너무 봄/가까이만 봄 | 1.0 → 0.75 → 0 | 0이면 예전 모멘트만 |
| 7 | `control_cutting_idx` | BEV 위쪽 노이즈 | 160 → 200 (더 자름) | 너무 자르면 lookahead 소멸 |
| 8 | `lane_lost_speed` | 마스크가 자주 끊김 | 30 → 0 (완전 정지) | 잠깐 끊길 때마다 멈춤 |

```bash
ros2 param set /motion_planner_node steer_k 0.035
ros2 param set /motion_planner_node steer_alpha 0.6
ros2 param set /lane_info_extractor_node near_blend 0.75
```

`model`과 `src_*`(IPM)는 재런치가 필요하다 — [launch-args.md](launch-args.md) §4.

### 일부러 안 하는 것

| 아이디어 | 안 하는 이유 |
|---|---|
| `path_planner` 되살려 스플라인 조향 | bag 스윕에서 차선면 중심이 이겼다. 되돌릴 근거가 없다 |
| 미분항(D) 추가 | `steer_alpha`/`steer_rate`로 이미 감쇠가 있다. 게인 3개는 실차에서 못 잡는다 |
| 좌우 비대칭 조향 | 지금 대칭으로 2랩이 돈다. 대칭이 안 될 때만 |
| 남의 팀 숫자 복붙 | [external-references.md](external-references.md) 금지 목록 |

---

## 4. 증상 → 어디를 만지나

| 증상 | 인지? 제어? | 먼저 |
|---|---|---|
| 정지 상태에서도 lane2 없음 | 인지 | 가중치 스왑, `threshold` 0.4, 카메라 `match_train` |
| 마스크는 있는데 중심이 nan | extractor | `control_min_area`↓, `control_cutting_idx`↓ |
| 직선에서 좌우로 흔들림 | 제어 과대 | `steer_k`↓ → `steer_alpha`↓ → `steer_rate`↓ |
| 첫 코너에서 늦게 돌거나 밖으로 | 둘 다 가능 | A/B 가중치 → 같으면 `drive_speed`↓ |
| S자에서 한 쪽만 깎음 | 마스크 끊김 또는 과대 | psh vs teamop |
| 갑자기 속도 30으로 기어감 | `lane_lost` | 로그에서 `ctrl=lane_lost` 확인 → 인지 문제 |
| 출발을 안 함 | `wait_green` 또는 `wait_lane` | 로그 확인. `/force_start` 또는 `require_green_start:=false` |
| 2랩 전에 멈춤 | 라이다 오검출 | `front_min` 로그. `lidar_stop_rmax`↓ |
| 명령은 나오는데 안 돎 | 하드웨어 | 가변저항 엔드스톱, 시리얼, 모니터 OFF |

인지로 메울 것과 제어로 메울 것:

- 마스크가 **아예 없음** → 학습. 게인으로 안 메워진다.
- 마스크는 있는데 **중심이 한쪽으로 0.5차선** → BEV·`vehicle_center_x`. `steer_k`를 키우면 진동만 커진다.
- 마스크·중심은 맞는데 **코너에서 못 따라감** → `drive_speed`·`steer_rate`.

### 로그 읽기

`motion_planner_node`가 매 틱 한 줄을 찍는다. 별도 디버그 토픽은 없다 (`control_debug`는 이 로그 문자열의 일부다).

```
steering: -3, left_speed: 250, right_speed: 250 hits=0/3 src=none tl=0 front_min=1.842
  ctrl=surface center=251.7 area=18422 err=-68.3 raw=-3.01 ema=-3.01 limited=-3.01
```

| 필드 | 보는 법 |
|---|---|
| `ctrl=` | `surface` 정상 · `lane_lost` 차선 놓침 · `wait_lane` 아직 출발 전 |
| `err` | 중심 오차(px). 부호가 0.1초마다 뒤집히면 게인/속도 과대 |
| `raw` → `ema` → `limited` | 세 값이 크게 벌어지면 필터·슬루가 걸리는 중 |
| `front_min` | 라이다 전방 최소거리. 0.12~0.95면 정지 후보 |
| `hits=n/3` | 정지 판정 연속 히트 |

```bash
ros2 topic echo /topic_control_signal      # 최종 명령
ros2 topic echo /lane_control_info --once  # 중심 x
ros2 topic echo /finish_stop_reason        # 왜 멈췄나
```

---

## 5. 8/13 계획 대비 무엇이 들어갔나

| 옛 노브 | 지금 | 형태 |
|---|---|---|
| P0-1 속도↓ | ✅ 파라미터화 | `drive_speed` (다만 기본이 **250**으로 올라갔다) |
| P0-2 기울기 deadband | ➖ 불필요 | slope 자체를 안 쓴다. 대신 `steer_k` 비례라 작은 오차엔 작은 조향 |
| P0-3 경로 없음 = 감속 | ✅ 구현 | `lane_timeout` 0.35s → `lane_lost_speed` 30 |
| P0-4 `steer_max` 5/6 | ➖ 미적용 | 7 유지. 비례 제어라 포화가 드물다 |
| P1-5 직선/코너 속도 분기 | ❌ 미구현 | 단일 `drive_speed`. TEAMMODE 브랜치 아이디어 → [archive](archive/README.md) |
| P1-6 BEV / car_center | ✅ 파라미터화 | `vehicle_center_x`, `control_cutting_idx`, `bev_calibrate.launch.py` |
| P1-7 비대칭 조향 | ❌ 미구현 | 대칭 유지 |
| P1-8 조향 slew | ✅ 구현 | `steer_rate` (기본값은 사실상 꺼짐) |
| P2 `atan(kp·slope)` | ➖ 다른 방식 | 픽셀 오차 선형 P로 갔다 |
| P2 속도 160–255 | ✅ 채택 | 저속 완주 후 250까지 올림 |

미구현 2개(직선/코너 분기, 비대칭)는 팀원 `TEAMMODE` 브랜치에 시제품이 있다. 실차 미검증이라 트렁크에는 안 넣었고 패치로만 보관한다 — [archive/README.md](archive/README.md).

---

## 6. 실험 시트 (복사용)

한 주행에 한 줄. 가중치와 제어 노브를 **둘 다** 적는다.

| 시각 | 가중치 | drive_speed | steer_k | alpha | rate | 직선 | 첫 코너 | S자 | 이탈 위치 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|
| | teamop | 250 | 0.044 | 1.0 | 7.0 | | | | | 현재 기본 |
| | teamop | 180 | 0.044 | 1.0 | 7.0 | | | | | 속도만 |
| | teamop | 250 | 0.035 | 1.0 | 7.0 | | | | | 게인만 |
| | best_psh | 250 | 0.044 | 1.0 | 7.0 | | | | | 인지 A/B |

통과 기준: 직선에서 실선·점선을 연속으로 넘지 않음 · 코너 스톨 없음 · 구조물 비접촉 · 2랩 후 정차.

끝난 뒤: 가중치가 바뀌면 **같은 제어 숫자**로만 모델을 갈아 끼운다. 제어와 인지를 같은 주행에서 같이 바꾸지 않는다.
