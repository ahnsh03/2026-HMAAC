# 저속 튜닝 → 미션 (Step D · E)

목적: 인지가 붙은 뒤 **느려도 이탈 없이** 차로를 따라가게 하고, 그다음 미션을 완성한다.

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
ros2 launch launch_pkg main.launch.py model:=weights/teamop_best.pt
# 차선만 A/B: model:=weights/best_psh.pt
# race는 drive_speed 파라미터가 없을 수 있음 (코드 70 고정). 상세: controller-tuning.md
```

정지(또는 바퀴 든 상태)에서:

```bash
ros2 topic echo /topic_control_signal
# steering / left_speed / right_speed 가 주기적으로 갱신되는지
```

- [ ] `/topic_control_signal` 발행 확인
- [ ] 조향·속도 명령을 바꾸면 모터가 반응하는지 확인 (저속)

---

## 2. 튜닝 노브 (효과 큰 순)

| 노브 | 어디서 | 첫 주행 권장 | 비고 |
|------|--------|--------------|------|
| `drive_speed` | launch / motion | **50–60** | 안정화 후 80→100↑ |
| `steer_max` | launch / motion | **7** (ino와 일치) | 진동 심하면 일시↓ |
| `model` / `threshold` | launch / yolov8 | `best.pt` / 0.5 | 미검출↓ → conf↓ |
| `device` | launch / yolov8 | 가능하면 `cuda:0` | 인지 끊김 완화 |

코드 기본값: [`motion_planner_node.py`](../../src/decision_making_pkg/decision_making_pkg/motion_planner_node.py) 의 `DEFAULT_DRIVE_SPEED=60`, `DEFAULT_STEER_MAX=7`.

예:

```bash
# 더 느리게
ros2 launch launch_pkg main.launch.py model:=best.pt drive_speed:=40

# 인지 conf 완화
ros2 launch launch_pkg main.launch.py model:=best.pt threshold:=0.3 drive_speed:=50
```

증상별:

| 증상 | 먼저 의 것 |
|------|----------------|
| 차선 안 보임 · 직진만 | YOLO `best.pt` · conf · 카메라 각도 |
| 한쪽으로 치우침 | 차로 추정/카메라 장착 · (가능하면) 오프셋 |
| 코너에서 이탈 | 속도↓ · 조향이 실제로 도는지(가변저항) |
| 직진 떨림 | 속도↓ · 인지 잡음 · steer 급변 |
| 명령은 나오는데 안 움직임 | 시리얼 포트·권한·모니터 충돌·배터리 |

---

## 3. 코스 연습 순서

1. **직선** — 차로 중앙 유지되는가  
2. **완만 코너** — 이탈 없이 따라가는가  
3. **한 바퀴** — 저속으로 완주  
4. 속도만 조금씩 올리기 (`drive_speed` 10단위)

통과 기준 (저속):

- [ ] 직선에서 실선·점선을 연속으로 넘지 않는다
- [ ] 코너에서 스톨(5초 정지) 없이 통과
- [ ] 랩타이머·구조물에 닿지 않는다

---

## 4. 미션 완성 (Step E)

규정 요약: 2차선 · 반시계 · **2바퀴** · 4분 · **초록 후** 출발 · 종료 **물체 탐지 정지**.

### 4-1. 신호등 (Stage 2)

[`main.launch.py`](../../src/launch_pkg/launch/main.launch.py)에서 `traffic_light_detector_node` 주석 해제 후 재launch.

- [ ] 빨간/출발 전: 정지 유지
- [ ] 초록 감지 후에만 출발 (조기 출발 = a2)

### 4-2. 라이다 종료 정지 (Stage 3)

`lidar_publisher` / `processor` / `obstacle_detector` 주석 해제.

- [ ] 2바퀴 후 물체 탐지 → 정지
- [ ] 앞바퀴는 정지선 앞, 뒷바퀴는 선 뒤 (아니면 a3/a4)

### 4-3. 최종 체크

[dev-checklist.md](../06-final-eval/dev-checklist.md) 전체.

피해야 할 네 가지: **조기 출발 · 이탈 · 스톨 · 랩타이머 충돌**.

---

## 5. 시뮬에서 가져올 감각 (이식은 나중)

시뮬 `SOLUTION.md`의 순수추종·곡률 앞먹임은 **감각 참고**용.  
내일 1순위는 Course 베이스 + `best.pt` + 저속 `drive_speed` 이다.  
시뮬 motion을 실차에 이식하는 것은 저속 완주 이후에 검토한다.
