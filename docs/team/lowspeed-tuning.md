# 속도 튜닝 → 미션 (Step D · E)

목적: 인지가 붙은 뒤 **이탈 없이** 차로를 따라가게 하고, 그다음 미션을 완성한다.

> 이 문서는 `drive_speed=60` 저속 1바퀴가 목표이던 때(8/13) 쓰였다.
> race가 저속 완주를 끝내고 **기본을 250**까지 올렸으므로, 아래는 "낮은 데서
> 올린다"가 아니라 **"현재 250에서 문제가 나면 내린다"** 로 읽는다.
> 제어 상수의 의미는 [controller-tuning.md](controller-tuning.md).

관련: [controller-tuning.md](controller-tuning.md) · [teamop-vs-team14.md](teamop-vs-team14.md) · [repo-structure-and-realcar-guide.md](repo-structure-and-realcar-guide.md) · [dev-checklist.md](../06-final-eval/dev-checklist.md)

---

## 1. 안전 · 정지 디버깅

- [ ] 조교 확인 · SMPS 12.0V · 주변을 비운다
- [ ] Arduino 시리얼 모니터 **OFF**
- [ ] `serial_sender`가 launch에 켜져 있는지 확인 (`main.launch.py`)

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash && source install/setup.bash
colcon build --symlink-install --packages-select decision_making_pkg launch_pkg

# 처음 굴릴 때는 기본 250 말고 낮춰서 시작한다
ros2 launch launch_pkg main.launch.py drive_speed:=50
# 차선만 A/B: model:=$HOME/ros2_ws/weights/best_psh.pt
# 초록 대기 건너뛰기: require_green_start:=false
```

`model`을 안 적으면 `weights/teamop_best.pt`가 자동으로 잡힌다 — [`weights/README.md`](../../weights/README.md).

정지(또는 바퀴 든 상태)에서:

```bash
ros2 topic echo /topic_control_signal
# steering / left_speed / right_speed 가 주기적으로 갱신되는지
```

- [ ] `/topic_control_signal` 발행 확인
- [ ] 조향·속도 명령을 바꾸면 모터가 반응하는지 확인 (저속)

---

## 2. 튜닝 노브 (효과 큰 순)

| 노브 | 어디서 | 현재 기본 | 비고 |
|------|--------|:---------:|------|
| `drive_speed` | launch / motion | **250** | 처음 굴릴 땐 50부터. 이탈하면 내린다 |
| `steer_k` | launch / motion | **0.044** | 직선 흔들림이면 0.035로 |
| `steer_max` | launch / motion | **7** | ino `MAX_STEERING_STEP`과 일치 |
| `steer_alpha` | launch / motion | **1.0** (EMA 꺼짐) | 채터가 남으면 0.6 |
| `steer_rate` | launch / motion | **7.0** (슬루 거의 꺼짐) | 급변 막으려면 3.0 |
| `model` | launch / yolov8 | 자동 (`teamop_best.pt`) | 목록: [weights/README.md](../../weights/README.md) |
| `threshold` | **yolov8 노드 파라미터** | `0.5` | main 인자가 **아니다**. 아래 param set |

코드 기본값: [`motion_planner_node.py`](../../src/decision_making_pkg/decision_making_pkg/motion_planner_node.py) 상단 상수.
launch 인자 전체: [launch-args.md](launch-args.md).

예:

```bash
# 더 느리게
ros2 launch launch_pkg main.launch.py drive_speed:=40

# 주행 중에 바로 (재런치 없이)
ros2 param set /motion_planner_node drive_speed 120
ros2 param set /motion_planner_node steer_k 0.035

# 인지 conf 완화 — threshold 는 launch 인자가 아니다
ros2 param set /yolov8_node threshold 0.3
```

증상별:

| 증상 | 먼저 의 것 |
|------|----------------|
| 차선 안 보임 · 직진만 | 가중치 스왑 · `threshold`↓ · 카메라 각도 |
| 한쪽으로 치우침 | `vehicle_center_x`(320) 재측정 · `bev_calibrator` |
| 코너에서 이탈 | `drive_speed`↓ · 조향이 실제로 도는지(가변저항) |
| 직진 떨림 | `steer_k`↓ → `steer_alpha`↓ → `drive_speed`↓ |
| 갑자기 속도 30으로 기어감 | `ctrl=lane_lost`. 인지가 0.35초 넘게 끊긴 것 |
| 명령은 나오는데 안 움직임 | 시리얼 포트·권한·모니터 충돌·배터리 |

---

## 3. 코스 연습 순서

1. **직선** — 차로 중앙 유지되는가  
2. **완만 코너** — 이탈 없이 따라가는가  
3. **한 바퀴** — 저속으로 완주  
4. 속도만 조금씩 올리기 (`drive_speed` 10단위 → 기본 250까지)

통과 기준 (저속):

- [ ] 직선에서 실선·점선을 연속으로 넘지 않는다
- [ ] 코너에서 스톨(5초 정지) 없이 통과
- [ ] 랩타이머·구조물에 닿지 않는다

---

## 4. 미션 완성 (Step E)

규정 요약: 2차선 · 반시계 · **2바퀴** · 4분 · **초록 후** 출발 · 종료 **물체 탐지 정지**.

### 4-1. 신호등 (Stage 2)

`traffic_light_detector_node`는 [`main.launch.py`](../../src/launch_pkg/launch/main.launch.py)에서 **항상 켜진다.** 끄는 인자는 없다.

- [ ] 빨간/출발 전: 정지 유지 (로그 `wait_green`)
- [ ] 초록 3틱 연속 후에만 출발 (조기 출발 = a2)
- [ ] 초록을 못 봐도 `green_start_timeout` 15초 뒤 자동 출발한다는 점을 인지할 것.
      대회에서 이 자동 출발이 곤란하면 `green_start_timeout:=0`으로 무한 대기시킨다.

구간 테스트만 할 때: `require_green_start:=false` 또는 `/force_start` ([wait-green.md](wait-green.md)).

### 4-2. 라이다 종료 정지 (Stage 3)

라이다 3노드는 `main.launch.py`에서 **항상 켜진다.**
정지 판정은 `lidar_lane1_min`이 `lidar_stop_rmin`(0.12) ~ `lidar_stop_rmax`(0.95) 안에
`need_finish_hits`(3틱) 연속으로 들어올 때다. **신호등 박스는 조건이 아니다.**

- [ ] 2바퀴 후 물체 탐지 → 정지
- [ ] 앞바퀴는 정지선 앞, 뒷바퀴는 선 뒤 (아니면 a3/a4)
- [ ] 조기 정지가 나면 `ros2 topic echo /finish_stop_reason` 과 로그 `front_min` 확인

### 4-3. 최종 체크

[dev-checklist.md](../06-final-eval/dev-checklist.md) 전체.

피해야 할 네 가지: **조기 출발 · 이탈 · 스톨 · 랩타이머 충돌**.

---

## 5. 시뮬에서 가져올 감각 (이식은 나중)

시뮬 `SOLUTION.md`의 순수추종·곡률 앞먹임은 **감각 참고**용.  
실차는 BEV 차선면 중심 P 제어로 2랩이 돈다. 시뮬 motion 이식은
지금 구조를 바꿔야 하므로, 바꿀 이유가 생겼을 때만 검토한다.
