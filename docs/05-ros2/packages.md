# ROS2 패키지 구성

출처: PDF p.142–147

## 오프라인에서 다루는 패키지

| 경로 | 역할 |
|---|---|
| `src/launch_pkg` | `main.launch.py`로 노드 일괄 기동 |
| `src/serial_communication_pkg` | `serial_sender_node` — MotionCommand → `/dev/ttyACM0` @115200 |
| `src/control/` | Arduino 펌웨어 (`driving.ino`, 점검용 ino) |
| `src/data_collection/` | 수동 수집 스크립트 (ROS 노드 아님) |

나머지 인지·결정 패키지는 온라인 사전학습 대상 (camera / lidar / decision / interfaces / debug).

## 실행 예

```bash
ros2 launch launch_pkg main.launch.py
```

`main.launch.py`에서 **serial_sender는 실차용으로 활성화**되어 있다.  
신호등·라이다 노드는 미션 단계에서 주석 해제한다.  
단계·인자: [team/repo-structure-and-realcar-guide.md](../team/repo-structure-and-realcar-guide.md) · [team/lowspeed-tuning.md](../team/lowspeed-tuning.md)

## serial_sender

- ROS2 ↔ 하드웨어 브리지
- 포트·보드레이트: `/dev/ttyACM0`, 115200

## control 펌웨어

- `driving.ino`: `s{조향}`, `l{좌}`, `r{우}` 파싱 + 가변저항 피드백 (±MAX_STEERING_STEP)
- `motor_test.ino` / `check_variable_resistor.ino`: 점검·보정용
