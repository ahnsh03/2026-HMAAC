# 실차용 YOLO 가중치 배치

이 폴더에 공개·검증 후보 `.pt`를 두었다. 시뮬 `sim.pt`는 두지 말 것.

절차·라벨 일람·**왜 이 테스트 순위인지**: [`docs/team/yolo-weights.md`](../../../../docs/team/yolo-weights.md)  
참고 레포 URL: [`docs/team/external-references.md`](../../../../docs/team/external-references.md)

extractor는 클래스 **이름**(`lane2`, `traffic_light`)으로 필터한다. 인덱스 0 = 차선이 아니다.

## 파일 · 테스트 순서

| 순위 | 파일 | 출처 | 학습 라벨 | 비고 |
|:---:|------|------|-----------|------|
| **1** | `teamop_best.pt` | hyeyeonIm/TeamOP | `lane2`,`object`,`traffic_light` | `H_merge_all-1` · **주행 기본** |
| **2** | `best_psh.pt` | 팀원 학습 2026-08-13 | `lane2`,`traffic_light` | yolo11s-seg · 차선 A/B · **신호등 약함** |
| — | `team14_best.pt` | 14팀 · 실차 `~/ros2_ws/best.pt` | `box`,`lane2`,`traffic_light`,`undefined` | Kingo-Car-1 · **파이프라인 확인만** |
| 3 | `youngsangc_best.pt` | youngsangc/H-Mobility-… | `lane2`,`traffic_light` | Kingo-Car-4 · 100ep |
| 4 | `1taekim_ti_best.pt` | 1TAEKIM | `lane2`,`traffic_light` | 같은 Kingo-Car-1 · 정보량 작음 |
| 5 | `1taekim_best.pt` | 1TAEKIM | `lane2`,`traffic_light` | 20ep · `data.yaml` |
| 6 | `cms1575_best.pt` | cms1575/autonomous_vehicle_SKKU | `lane1`,`lane1_car`,`lane2`,`lane2_car`,`traffic_light` | m-seg ~52MB |
| — | `hlhl_best.pt` | gustj5092/HLHL | `lane`,`road` | **차선 드롭인 금지** |
| — | `hlhl_best_new.pt` | HLHL | `lane` | nano · 금지 |
| — | `hlhl_traffic_light.pt` | HLHL | 신호 색 클래스 | 세그 노드와 별개 · 참고만 |

시간 없으면 **`teamop`만**. `best_psh`는 차선 A/B(신호등 약함). `best_psh_v2.pt`는 race `weights/`에만 있고 **차선 없음 · 주행 금지**.

## Launch 예

```bash
W=$HOME/ros2_ws/src/camera_perception_pkg/camera_perception_pkg/weights
# 실차 race면: W=$HOME/ros2_ws/weights

ros2 launch launch_pkg perception_debug.launch.py \
  model:=$W/teamop_best.pt device:=cuda:0 cam_num:=0
# model:=$W/best_psh.pt
```

워크스페이스 루트에 심볼릭/복사를 두고 `model:=best.pt`로 써도 된다. 실차 노트북의 `~/ros2_ws/best.pt`가 팀 학습본 `team14_best`이다. `best_psh`는 루트 `best.pt`와 **다른 파일**.

```bash
# 루트 후보를 팀 학습본으로 (기본)
cp $W/team14_best.pt $HOME/ros2_ws/best.pt
```
