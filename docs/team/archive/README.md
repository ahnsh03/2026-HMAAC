# 폐기 브랜치 백업 — 팀원 제어기 시도 (newmp · TEAMMODE)

목적: 대회 중 갈라진 사이드 브랜치를 지우기 전에 **차이분을 패치로 남긴다**.  
결론부터: **두 브랜치 코드는 `src/`에 반영하지 않는다.** 실차 검증이 없고, `newmp`는 실행조차 안 된다.

관련: [controller-tuning.md](../controller-tuning.md) · [lowspeed-tuning.md](../lowspeed-tuning.md) · [cheat-sheet.md](../cheat-sheet.md)

날짜: 2026-08-19 백업. 원본 커밋일 2026-08-13.  
기준(merge-base): `3beba99` — "Make teamop the default driving weights."

---

## 0. 한 줄

| 브랜치 | 원본 커밋 | 작성자 | 상태 | 판단 |
|--------|-----------|--------|------|------|
| `TEAMMODE` | `cd76bf3` | qkrtjdghks2002 | 문법 정상, **실차 미검증** | 아이디어만 참고 |
| `newmp` | `65c20a3` | seulhawon0414 | **실행 불가 (들여쓰기 붕괴)** | 아이디어만 참고 |

실제 주행에 쓴 제어기는 당시 `race` 브랜치다. 두 브랜치와 계보가 다르다 — `race`는 BEV 중심 오차 P 제어(`steer_k`), 아래 둘은 경로 기울기(slope) 기반이다.

`race`는 이후 `main`에 병합되고 `race-final-2026-08-14` 태그로 박제한 뒤 삭제했다. 지금 브랜치는 `main` 하나다.

```
                    ┌─ cd76bf3  TEAMMODE
3beba99 ── 2026 ────┤
                    └─ 65c20a3  newmp
   │
ee9df9a ──────────────  8c09832  race   ← 실제 주행
```

---

## 1. 파일

| 파일 | 원본 | 규모 |
|------|------|------|
| `2026-TEAMMODE-cd76bf3.patch` | `3beba99..TEAMMODE` | 3 파일, +76 / −26 |
| `2026-newmp-65c20a3.patch` | `3beba99..newmp` | 1 파일, +57 / −39 |

`git format-patch` 원본이라 작성자·날짜·커밋 메시지·원본 SHA가 그대로 들어 있다.

### 되살리는 법

```bash
git checkout -b restore-teammode 3beba99
git am docs/team/archive/2026-TEAMMODE-cd76bf3.patch
```

`3beba99` 위에서만 깨끗이 적용된다. 지금 `main` 끝에 얹으면 충돌한다.

---

## 2. `TEAMMODE` (cd76bf3) — 조향 비례제어 + 코너 감속

바꾼 파일: `src/control/driving/driving.ino` · `src/decision_making_pkg/decision_making_pkg/motion_planner_node.py` · `src/launch_pkg/launch/main.launch.py`

### 2.1 `driving.ino` — 조향 PWM을 on/off에서 비례로

| | 기존 | TEAMMODE |
|--|------|----------|
| 조향 구동 | `STEERING_SPEED = 128` 고정 | `MIN_STEERING_PWM 80` ~ `MAX_STEERING_PWM 200` |
| 판정 | `mapped_resistance == angle` 비교 | 목표 저항값 역산 후 오차 `res_error` |
| 게인 | 없음 | `KP_STEER = 3.5` (`pwm = 80 + 3.5 × |오차|`) |
| 정지대 | 없음 | `DEADBAND_RESISTANCE = 4` |

`steerLeft()` / `steerRight()`가 `speed` 인자를 받도록 시그니처가 바뀐다.

### 2.2 `motion_planner_node.py` — slope 이진 → 비례 양자화

기존은 slope 부호만 보고 `±steer_max`를 던졌다. TEAMMODE는 각도에 비례시킨다.

```python
steer_float = (target_slope / self.max_slope_angle) * self.steer_max
```

| 파라미터 | 기본 | 의미 |
|----------|------|------|
| `max_slope_angle` | `35.0` | 이 각도(도)에서 `steer_max`가 나온다 |
| `slope_deadband` | `2.0` | 이 미만은 직진(조향 0) |
| `drive_speed_straight` | `drive_speed + 15` (launch 기본 `75`) | 직진 가속 |
| `drive_speed_corner` | `max(20, drive_speed - 15)` (launch 기본 `45`) | 코너 감속 |
| `straight_steer_threshold` | `1` | 조향 절댓값이 이 이하면 직진 속도 |

조향 크기에 따라 straight↔corner를 선형 보간한다. `target_slope == 'inf'`(수직, `p1_y == p2_y`) 처리도 추가했다 — [`decision_making_function_lib.py:49`](../../../src/decision_making_pkg/decision_making_pkg/lib/decision_making_function_lib.py)가 실제로 문자열 `'inf'`를 반환하므로 이 비교는 의도대로 동작한다.

### 2.3 `main.launch.py`

`drive_speed_straight` / `drive_speed_corner`를 launch 인자로 노출하고 `motion_planner_node`에 전달한다.

### 왜 안 썼나

실차에서 한 번도 돌려보지 않았다. `max_slope_angle=35`, `KP_STEER=3.5`, 75/45 속도는 전부 책상 위 추정값이다. 특히 `driving.ino` 변경은 **조향 모터 PWM을 직접 건드리므로** 미검증 상태로 올리면 실차에서 조향이 튀거나 못 따라갈 위험이 있다.

---

## 3. `newmp` (65c20a3) — P 제어 + 조향 변화율 제한

바꾼 파일: `motion_planner_node.py` 하나.

의도한 것:

| 항목 | 값 |
|------|-----|
| `KP` | `3.0` (`target_steering = KP × slope`) |
| `MAX_STEERING` | `7` |
| `MAX_STEERING_CHANGE` | `1` — 한 주기(0.1초)당 조향 1스텝까지만 |

### 실행 불가

"조향 변화량 제한" 블록이 **들여쓰기 0칸, 모듈 레벨**로 나와 있다. 클래스 밖에서 `self`를 참조하므로 임포트 시점에 터진다.

```python
# ------------------------------------------------
# 조향 변화량 제한
# ------------------------------------------------
steering_diff = target_steering - self.steering_command   # ← 클래스 밖
```

그 외 회귀:

- `drive_speed` / `steer_max` 파라미터를 **삭제**하고 속도를 `100`으로 하드코딩
- `control_debug` 퍼블리셔와 `_last_reason` 계보를 삭제 → [debug-and-incremental-test.md](../debug-and-incremental-test.md)의 디버그 경로가 끊긴다
- `self.KP` / `self.MAX_STEERING` / `self.MAX_STEERING_CHANGE`가 `__init__`에 **중복 정의**

커밋 본인도 첫 줄에 "아마 하파 튜닝은 차량의 주행을 보고 수정하면서 해야할 것 같습니다"라고 적어 두었다. 미완성 상태로 올린 것이다.

---

## 4. 살릴 만한 아이디어

`race`의 P 제어를 더 손볼 일이 생기면 이 둘에서 가져올 것은 두 가지다.

1. **조향 변화율 제한(slew)** — `newmp`의 `MAX_STEERING_CHANGE`. `main`에는 이미 `steer_rate`로 들어가 있다(기본 `7.0` = 사실상 꺼짐). 조향이 튈 때 이 값을 낮추면 된다.
2. **코너 감속** — `TEAMMODE`의 straight/corner 이원화. `main`은 `drive_speed` 단일값이라, 코너 이탈이 문제면 여기서 출발할 수 있다.

`driving.ino`의 비례 PWM은 실차 포텐셔미터 캘리브레이션([potentiometer-calibration.md](../../03-hardware/potentiometer-calibration.md))을 다시 잡은 뒤에만 검토한다.
