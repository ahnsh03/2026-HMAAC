# 초록 출발 (WAIT_GREEN)

상태: **`2026` 트렁크에 구현됨** (`bc60881` + `/force_start` + 15초 타임아웃 `8c09832`).  
전제: 간략 미션은 출발선에서 적 → 첫 녹만 보고 출발. 랩 중 신호등으로 랩을 세지 않음.  
관련: [controller-tuning.md](controller-tuning.md) · [tl-hsv-tuning.md](tl-hsv-tuning.md) · [mission-strategy.md](../06-final-eval/mission-strategy.md) · [verbal-briefing.md](../06-final-eval/verbal-briefing.md)

**범위:** 이 문서는 **출발 게이트(WAIT_GREEN)** 만.  
랩2 **종료 정지**는 별도 — 팀 논의안은 `좌측 1차로 차량 AND 신호등 박스≈Npx` ([mission-strategy.md](../06-final-eval/mission-strategy.md) «단순 정지 휴리스틱»). 출발용 적색 `y_max`와 종료용 조건을 섞지 말 것.

---

## 0. 왜 제어 튜닝보다 먼저인가

`motion_planner`는 **출발 전** 속도 0이다. `Green`이 0.3초 연속(`need_green_hits`=3틱)이거나 `/force_start`가 true면 `drive_speed`(기본 **250**)로 차선을 따라간다.
`traffic_light_detector_node`는 `main.launch.py`에서 **항상 켜진다.** 끄는 인자는 없다.

**자동 출발 타임아웃:** 초록을 못 보면 `green_start_timeout`(기본 **15.0초**) 뒤에 스스로 출발한다. 무한 대기시키려면 `green_start_timeout:=0`.

출발 게이트를 먼저 잠그면 이후 속도·deadband 실험이 “이미 출발한 차”만 본다.

---

## 1. 이미 있는 것 / 없는 것

있는 것 (새로 만들지 말 것):

| 조각 | 위치 | 하는 일 |
|------|------|---------|
| YOLO 박스 | `yolov8_node` | `class_name == traffic_light` |
| HSV 색 | `traffic_light_detector_node` → `get_traffic_light_color` | `Red` / `Yellow` / `Green` / `Unknown`, 없으면 `None` |
| 토픽 | `/yolov8_traffic_light_info` (`std_msgs/String`) | 위 문자열 |
| 적색 근접 정지 | `motion_planner` `y_max < 150` | **출발 게이트가 아님.** 이미 달리는 중 적색 처리 |

없는 것 (당시): 출발 전 정지 · 첫 Green 래치. **지금은 `race` `motion_planner`에 있음.**

cms1575의 `traffic_stop → green → lane2_drive`와 같은 아이디어만 가져온다. FSM 파일·모드 문자열 전체를 복사하지 않는다.

---

## 2. 최소 변경 단위 (구현 시 이 두 곳만)

다른 노드·YOLO·extractor는 손대지 않는다. HSV는 13일 튜닝분을 그대로 쓴다.

### A. `main.launch.py` — 주석 해제 (신규 코드 0줄)

`traffic_light_detector_node` 블록만 켠다. 라이다 세 노드는 꺼 둔다.

### B. `motion_planner_node.py` — 래치 한 개 (~15줄)

`timer_callback` **맨 위**(라이다·적색 분기보다 앞)에만 넣는다.

```text
started = False          # 노드 수명 동안 한 번만 True
green_hits = 0
NEED = 3                 # 0.1s 주기 × 3 = 0.3s 연속 Green

매 주기:
  color = traffic_light_data.data if 있으면 else "None"

  if not started:
      if color == "Green":
          green_hits += 1
          if green_hits >= NEED:
              started = True
      else:
          green_hits = 0
      if not started:
          steer = 0, speed = 0
          publish 후 return          # 기존 주행/적색 분기 안 탐
  # started == True 이면 지금 코드 그대로 (경로 추종)
```

규칙:

- **출발 조건은 `Green`뿐.** `not Red`로 출발하지 말 것. (`None`/`Unknown`/`Yellow`/`Red`는 대기)
- **한 번 출발하면 되돌리지 말 것.** 랩 중 적이 되어도 `WAIT_GREEN`으로 돌아가면 스톨·오정지. 기존 `y_max < 150` 적색 정지는 간략 미션에선 started 이후 **실행되지 않게** 두는 편이 안전하다 (랩2 적 전환은 내일 확인).
- detector String만 본다. motion에서 bbox를 다시 열지 않는다. 지금 적색 분기는 `detection_data is None`이면 크래시 가능하다. 새 게이트는 그 루프를 타지 않게 앞에 둔다.

이게 전부다. 상태머신 파일, 커스텀 메시지, YOLO 클래스 `green` 추가는 하지 않는다.

---

## 3. 의도적으로 안 넣는 것

| 넣지 말 것 | 이유 |
|------------|------|
| 랩 카운트 / LAP1·LAP2 | 출발 게이트와 별개. 나중에 |
| 색 변화로 랩 세기 | 랩 중 초록 유지가 기본 |
| HSV 범위 재튜닝 | **13일 기준으로 이미 함** ([tl-hsv-tuning.md](tl-hsv-tuning.md)). 이 PR에서 되돌리지 말 것 |
| 두 번째 YOLO (신호 전용) | 최소 단위 아님 |
| 주행 중 적색 정지 강화 | 간략 미션에선 출발 후 무시 |

선택(그래도 5줄 이하, 필요할 때만):

| 가드 | 언제 |
|------|------|
| `require_green_start` 파라미터 기본 True | 제어만 볼 때 False로 우회 |
| Green bbox가 화면 위쪽일 때만 인정 (`y_max < 200`) | 잔디가 박스에 들어와 거짓 Green이 날 때 |
| `force_start` 서비스/파라미터 | psh가 출발선에서 박스를 못 잡을 때 수동 해제 |

예전 `get_traffic_light_color`는 픽셀 비율이 전부 0이면 `Red`를 반환했다. **13일 튜닝에서 고침** — 꺼진/과대박스는 `Unknown`. 출발 게이트는 여전히 Green만 본다.

---

## 4. 가중치와 출발 게이트

같은 200장에서 신호등 **박스** 검출(conf 0.5):

| | TL이 있는 프레임 | 평균 TL conf | teamop만 잡은 프레임 |
|--|------------------|--------------|----------------------|
| teamop | 44 / 200 (22%) | 0.85 | 19 |
| best_psh | 25 / 200 (12.5%) | 0.77 | 0 |

psh는 teamop이 못 본 불을 추가로 잡지 못했다. 차선은 psh가 비슷하거나 곡선에서 더 진하다 ([teamop-vs-team14.md](teamop-vs-team14.md) § psh).

가져갈 운영:

1. **정지 상태, 출발선**에서 기본 `model:=teamop`으로  
   `ros2 topic echo /yolov8_traffic_light_info`  
   적·녹이 나오는지 확인한다. (detector 켠 뒤)
2. `best_psh`는 신호등이 약하니 게이트 검증에 쓰지 않는다. 차선만 A/B할 때 켠다.
3. `best_psh_v2`는 차선이 없으니 `model:=`에 넣지 않는다.

색은 HSV가 담당한다. YOLO가 `traffic_light` 박스만 주면 된다. 클래스에 `green`을 넣지 말 것.

---

## 5. 검증 순서 (코드 넣은 뒤)

모터 권한 없이:

1. detector ON, 출발선 정차, 빨간불 → `/yolov8_traffic_light_info` = `Red`, `/topic_control_signal` 속도 0
2. 불을 가리거나 모델이 놓침 → `None`/`Unknown`, 속도 0 유지
3. 초록으로 바꿈 → 0.3s 뒤 속도 70(또는 당시 값), `started` 유지
4. 다시 적으로 바꿔도 속도 0으로 돌아가지 않음 (간략 미션)

그다음 저속 1코너. 제어 튜닝 시트에 `wait_green=on`을 한 칸 적는다.

---

## 6. 구간 테스트 (모터 ON, 초록 없이 출발)

detector가 `/yolov8_traffic_light_info`를 계속 쓰기 때문에, **detector가 켜진 채로** `ros2 topic pub ... Green`을 한 번 쏘면 바로 `None`/`Red`에 덮인다. 아래 셋 중 하나를 쓴다.

### A. 정지해 두었다가 출발 명령 (권장)

기본 launch 그대로 (게이트 ON). 차가 속도 0으로 기다린 뒤:

```bash
ros2 topic pub --once /force_start std_msgs/msg/Bool "{data: true}"
```

`started` 래치만 연다. 이후 적색으로 다시 서지 않음 (간략 미션).

실행 중에 게이트만 끄기:

```bash
ros2 param set /motion_planner_node require_green_start false
```

다음 0.1s 틱부터 주행.

### B. launch부터 게이트 끄기

```bash
ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt \
  require_green_start:=false
```

켜자마자 `drive_speed`로 달린다. 코너만 볼 때는 `drive_speed:=50`을 같이 준다.

### C. 초록 토픽을 직접 쏘기

detector를 끄는 launch 인자는 **없다.** detector가 `Red`를 계속 쏘면 이 방법은 안 먹으니, 신호등이 안 보이는 자리에서 하거나 B(`require_green_start:=false`)를 쓴다. `Green`이 **0.3초 연속**(3틱)이어야 하므로 한 번이 아니라 주기 publish:

```bash
ros2 launch launch_pkg main.launch.py

# 다른 터미널. -r 10 → 0.3s면 충분
ros2 topic pub -r 10 /yolov8_traffic_light_info std_msgs/msg/String "{data: 'Green'}"
```

Ctrl+C로 pub을 멈춰도 이미 출발했으면 계속 달린다.

---

## 7. 구현 체크

- [x] `main.launch.py` detector 상시 ON (끄는 launch 인자는 없다)
- [x] `motion_planner`에 `started` / `green_hits` / 조기 return
- [x] started 이후 기존 적색 `y_max` 분기는 타지 않음
- [x] `/force_start`, `require_green_start` 런타임 변경
- [ ] 출발선 echo로 psh vs teamop 박스 확인
- [x] 랩 FSM·라이다 정지는 이 PR에 넣지 않음
