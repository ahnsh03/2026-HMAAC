# 실차용 YOLO 가중치 배치

이 폴더에 공개·검증 후보 `.pt`를 둔다. 시뮬 `sim.pt`는 두지 말 것.

절차·라벨 일람·**왜 이 테스트 순위인지**: [`docs/team/yolo-weights.md`](../docs/team/yolo-weights.md)  
실차 비교 근거: [`docs/team/teamop-vs-team14.md`](../docs/team/teamop-vs-team14.md)  
참고 레포 URL: [`docs/team/external-references.md`](../docs/team/external-references.md)

extractor는 클래스 **이름**(`lane2`, `traffic_light`)으로 필터한다. 인덱스 0 = 차선이 아니다.

## 파일 · 테스트 순서

| 순위 | 파일 | 출처 | 학습 라벨 | 비고 |
|:---:|------|------|-----------|------|
| **1** | `teamop_best.pt` | hyeyeonIm/TeamOP | `lane2`,`object`,`traffic_light` | `H_merge_all-1` · **주행 기본** |
| **2** | `best_psh.pt` | 팀원 학습 2026-08-13 | `lane2`,`traffic_light` | yolo11s-seg · 차선 A/B · **신호등 약함** |
| — | `best_psh_v2.pt` | 팀원 학습 2026-08-13 | 신호등 위주 | 신호등은 나아지나 **차선 없음 · 주행 금지** |
| — | `team14_best.pt` | 14팀 · 실차 `~/ros2_ws/best.pt` | `box`,`lane2`,`traffic_light`,`undefined` | Kingo-Car-1 · **파이프라인 확인만** |
| 3 | `youngsangc_best.pt` | youngsangc/H-Mobility-… | `lane2`,`traffic_light` | Kingo-Car-4 · 100ep |
| 4 | `1taekim_ti_best.pt` | 1TAEKIM | `lane2`,`traffic_light` | 같은 Kingo-Car-1 · 정보량 작음 |
| 5 | `1taekim_best.pt` | 1TAEKIM | `lane2`,`traffic_light` | 20ep · `data.yaml` |
| 6 | `cms1575_best.pt` | cms1575/autonomous_vehicle_SKKU | `lane1`,`lane1_car`,`lane2`,`lane2_car`,`traffic_light` | m-seg ~52MB |
| — | `hlhl_best.pt` | gustj5092/HLHL | `lane`,`road` | **차선 드롭인 금지** |
| — | `hlhl_best_new.pt` | HLHL | `lane` | nano · 금지 |
| — | `hlhl_traffic_light.pt` | HLHL | 신호 색 클래스 | 세그 노드와 별개 · 참고만 |

시간 없으면 **`teamop`만** 쓴다. `best_psh`는 차선 A/B 용이다.

## 자동 선택 — 보통은 `model:=`을 안 적어도 된다

`main.launch.py`의 `model` 기본값은 [`workspace_paths.py`](../src/launch_pkg/launch/workspace_paths.py)의 `default_yolo_weights()`가 정한다. 워크스페이스 루트를 찾아 아래 순서로 **처음 존재하는 파일**을 쓴다.

```
1. weights/teamop_best.pt     ← 이 레포에 있으므로 보통 여기서 결정된다
2. weights/best_psh.pt
3. best.pt                    ← 루트
4. weights/team14_best.pt
5. weights/best.pt
```

즉 `ros2 launch launch_pkg main.launch.py` 만 쳐도 `teamop_best.pt`가 잡힌다.

## 직접 지정할 때

```bash
W=$HOME/ros2_ws/weights

ros2 launch launch_pkg main.launch.py model:=$W/best_psh.pt
ros2 launch launch_pkg perception_debug.launch.py model:=$W/teamop_best.pt device:=cuda:0 cam_num:=0
```

`model`은 시작 때 한 번만 읽는다. 바꾸려면 launch를 다시 띄운다 —
[`docs/team/launch-args.md`](../docs/team/launch-args.md) §4.

루트 `best.pt`는 실차 노트북의 `~/ros2_ws/best.pt`(팀 학습본 `team14_best`)를 그대로 올린 것이다. `best_psh`와는 **다른 파일**이다.
