# 실차용 YOLO 가중치 배치

이 폴더에 공개·검증 후보 `.pt`를 두었다. 시뮬 `sim.pt`는 두지 말 것.

절차·분석: [`docs/team/yolo-weights.md`](../../../../docs/team/yolo-weights.md)  
참고 레포 URL: [`docs/team/external-references.md`](../../../../docs/team/external-references.md)

## 파일 · 테스트 순서

| 순위 | 파일 | 출처 | 비고 |
|:---:|------|------|------|
| 1 | `teamop_best.pt` | hyeyeonIm/TeamOP | `lane2`+`traffic_light` · **1순위** |
| 2 | `youngsangc_best.pt` | youngsangc/H-Mobility-… | 동일 클래스 |
| 3 | `1taekim_best.pt` | 1TAEKIM/H-Mobility-… | 실패 시 `1taekim_ti_best.pt` |
| 3b | `1taekim_ti_best.pt` | 1TAEKIM | 조명 변형 후보 |
| 4 | `cms1575_best.pt` | cms1575/autonomous_vehicle_SKKU | m-seg ~52MB |
| 5 | `hlhl_best.pt` | gustj5092/HLHL | 백업 |
| 5b | `hlhl_best_new.pt` | HLHL | nano급 |
| — | `hlhl_traffic_light.pt` | HLHL | 신호 전용 · 참고 |

## Launch 예

```bash
W=$HOME/ros2_ws/src/camera_perception_pkg/camera_perception_pkg/weights

ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt device:=cuda:0 drive_speed:=50
```

워크스페이스 루트에 심볼릭/복사를 두고 `model:=best.pt`로 써도 된다.

```bash
# 예: 루트에 현재 후보를 best.pt로
cp $W/teamop_best.pt $HOME/ros2_ws/best.pt
ros2 launch launch_pkg main.launch.py model:=$HOME/ros2_ws/best.pt device:=cuda:0
```
