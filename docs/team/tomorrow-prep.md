# 내일 실차 재개 체크리스트 (14팀)

목적: 오늘(8/12) 실차 시간이 끝난 뒤, **내일 바로 이어서** 하드웨어·수집·ROS 작업을 재개하기 위한 준비.

원본 흐름: [docs README](../README.md) · PDF I–V

## 오늘 끝내고 올 것 (퇴근 전)

- [ ] 배터리 **OFF**, SMPS/모터드라이버 이상 없음 확인
- [ ] 시리얼 모니터·수집/ROS 프로세스 모두 종료
- [ ] USB(카메라·Arduino·LiDAR) 정리 — 핫플러그로 장치명 꼬이지 않게
- [ ] [`vehicle-record-sheet.md`](../03-hardware/vehicle-record-sheet.md)에 끝값·장치명·선색 기입
- [ ] `driving.ino` 끝값/`MAX_STEERING_STEP` 커밋 또는 USB에 백업
- [ ] 팀 레포 `2026` 브랜치 push (로컬만 두지 말 것)
- [ ] 차량·배터리·부품박스 라벨(`H-모빌리티 14팀`) 확인

## 내일 도착 즉시

상세 체크: **[hw-boot.md](hw-boot.md)** (장치·시리얼·SMPS·가변저항)

- [ ] Wi-Fi (`SKKU_GUEST`) · 노트북 비번 `1234`
- [ ] `cd ~/ros2_ws && git pull` (팀 원격 `ahnsh03/2026-HMAAC` · 브랜치 `2026`)
- [ ] 가중치 8개 확인 (아래 §실차 pull)
- [ ] `source /opt/ros/humble/setup.bash && source install/setup.bash`
- [ ] `ls /dev/video* ttyACM* ttyUSB*` → 기록 시트와 비교, 변경 시 파라미터 수정
- [ ] `sudo chmod 777 /dev/ttyACM0` (장치명에 맞게)
- [ ] 가변저항 A2 배선·시리얼 모니터로 끝값 **재확인**(분해했다가 다시 조립한 경우)
- [ ] SMPS **12.0V** 확인 (조교 확인 전 배터리는 OFF)

## 실차 pull · 가중치 · 참고 클론 (`~/ref`)

팀 레포만 `~/ros2_ws`에 둔다. 개발 PC의 워크스페이스 `external/` 은 **실차에 없음**. 참고 코드는 **워크스페이스 밖** `~/ref`에 클론한다 (`colcon`이 섞이지 않게).

```bash
cd ~/ros2_ws
git pull
git log -1 --oneline

# 가중치 (이미 레포에 커밋됨 · ~194MB)
W=src/camera_perception_pkg/camera_perception_pkg/weights
ls -lh $W/*.pt
# 있어야 할 파일 8개:
#   teamop_best.pt  youngsangc_best.pt
#   1taekim_best.pt  1taekim_ti_best.pt
#   cms1575_best.pt
#   hlhl_best.pt  hlhl_best_new.pt  hlhl_traffic_light.pt

# pull 후 새 launch/debug 노드 반영
source /opt/ros/humble/setup.bash
colcon build --symlink-install \
  --packages-select launch_pkg debug_pkg camera_perception_pkg decision_making_pkg
source install/setup.bash
```

참고 레포는 **필요한 것만**. 전부 클론할 필요 없음. 적용/금지는 [external-references.md](external-references.md).

```bash
mkdir -p ~/ref && cd ~/ref
git clone --depth 1 https://github.com/hyeyeonIm/TeamOP.git
git clone --depth 1 https://github.com/1TAEKIM/H-Mobility-Autonomous-Advanced-Course.git
git clone --depth 1 https://github.com/cms1575/autonomous_vehicle_SKKU.git
# 동일 트랙 문서만 볼 때 (가중치·시리얼 드롭인 금지)
# git clone --depth 1 -b driving-obstacle-avoidance \
#   https://github.com/x2-qp-cheese/skku-ai-autonomous-driving-2026.git f23-driving
```

---

## 내일 작업 우선순위 (권장)

전체 지도: **[repo-structure-and-realcar-guide.md](repo-structure-and-realcar-guide.md)**  
미션(가규정): [verbal-briefing](../06-final-eval/verbal-briefing.md) · [strategy](../06-final-eval/mission-strategy.md) · [logging](../06-final-eval/logging-and-experiments.md)

1. [HW 부팅](hw-boot.md) — 장치·전원·시리얼
2. **소단위 디버그** — 카메라 → C920e → 인지(serial OFF) → IPM 트랙바 ([debug-and-incremental-test](debug-and-incremental-test.md))
3. **로깅 인프라** — `./scripts/run_session.sh` dry-run ([logging-and-experiments](../06-final-eval/logging-and-experiments.md))
4. **신호등 / 랩 카운트** — 출발 적→녹 · **랩2 적 전환 여부** · 정면 통과로 랩 구분(색으로 세지 말 것)
5. **정지 퓨전 실험** — 물체탐지 정석 + **규정집 정지 위치** · 출발점+30cm 차량 · FOV 상실·정차 cm
6. **차선 강건성** — 속도–페널티 ([lowspeed-tuning](lowspeed-tuning.md)) · YOLO [`yolo-weights`](yolo-weights.md)
7. (미완료 HW가 있으면) [전원](../03-hardware/power-wiring.md) · [제어](../03-hardware/control-wiring.md) · [프레임·라이다](../03-hardware/frame-and-lidar.md)

치트시트: [cheat-sheet.md](cheat-sheet.md)

## 최종평가 · 규정 대비

규정: [06-final-eval/rules.md](../06-final-eval/rules.md) · [dev-checklist.md](../06-final-eval/dev-checklist.md) · [penalties.md](../06-final-eval/penalties.md)  
가규정: [verbal-briefing.md](../06-final-eval/verbal-briefing.md) (룰미팅 후 갱신)

- [ ] SMPS **12.0V** · 센서 전후110/좌우60/높이75cm 이내
- [ ] 신호등 탐지 대기 → 초록 후 출발 (조기 출발 a2 방지)
- [ ] 2차선 · 반시계 · 2바퀴 · 4분 내 · 종료 정지 = **규정집**(앞·뒤 바퀴 vs 정지선) · a3/a4
- [ ] 1랩 무장애 · 랩2 도착 차량≈출발점+30cm · 물체탐지 정석·수단 자유
- [ ] FOV 상실 대비: 카메라만으로 최종 정지하지 않기 · LiDAR/지연 퓨전
- [ ] 랩 중 `red`를 출발 대기로 오인하지 않기 · **랩2 적불 여부** 룰미팅에서 확인
- [ ] 차선 침범(b3)·이탈(b1)·랩타이머 충돌(b4)·5초 스톨(b2) 대응
- [ ] `main.launch.py`: serial 활성 · 미션 시 **신호등·라이다** 주석 해제
- [ ] `best.pt` + `drive_speed` 저속 튜닝 ([yolo-weights](yolo-weights.md) · [lowspeed-tuning](lowspeed-tuning.md))
