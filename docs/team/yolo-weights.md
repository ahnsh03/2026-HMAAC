# YOLO 가중치 — Course `weights/` 드롭인 → (필요 시) Colab·Roboflow

목적: 실차에 차선(`lane2`)·신호등(`traffic_light`)이 잡히게 한다.  
시뮬 `sim.pt`는 쓰지 않는다.

관련: [external-references.md](external-references.md) · [weights/README.md](../../src/camera_perception_pkg/camera_perception_pkg/weights/README.md) · [repo-structure-and-realcar-guide.md](repo-structure-and-realcar-guide.md) · [lowspeed-tuning.md](lowspeed-tuning.md)

---

## 0. 권장 순서

| 순위 | 방법 | 언제 |
|:---:|------|------|
| **1** | `weights/*.pt` 드롭인 (아래 테스트 순서) | **내일 기본** |
| **2** | Colab + [`notebooks/kingo_car.ipynb`](notebooks/kingo_car.ipynb) | 웹 가중치가 조명·각도에서 깨질 때 |
| **3** | `data_collection` → 자체 라벨 → fine-tune | 최후 |

### Kingo Car는 “라벨만 있고 가중치가 없는가?”

| 구분 | 상태 |
|------|------|
| Roboflow **데이터셋** | `lane2`/`traffic_light` **라벨 있음** (train~1950). Universe가 비공개면 다운로드에 **팀 Roboflow API 키 + 접근 권한** 필요 |
| **이미 학습된 가중치** | `kingo_car.ipynb`로 그 데이터셋을 학습한 산출물이 TeamOP 계열 `best.pt`와 동일 계열 → Course **`teamop_best.pt` 등이 사실상 Kingo 학습본** |
| 지금 이 WSL에서 재학습 | GPU/NVML 차단 · ultralytics 미설치 · Roboflow 403 → **지금 당장 새 `.pt` 생성은 불가** |
| Colab에서 다시 학습 | 가능. `model=yolov8s-seg.pt`(스크래치) 또는 `model=teamop_best.pt`(파인튜닝) |
| 파인튜닝에 Kingo 쓰기 | **가능·권장**. 드롭인이 커튼/카메라각에서 약하면 Kingo(+현장 소수 장)로 `teamop_best.pt`를 추가 epoch |

정리: Kingo는 “아직 아무도 학습 안 한 raw”가 아니라 **라벨드 학습셋**. 우리는 그 결과물에 가까운 가중치를 이미 `weights/`에 넣어 두었고, 재학습은 **접근 권한 + Colab/실차 GPU**가 있을 때 백업·파인튜닝용이다.

---

## 1. HSV vs YOLO (이번 미션)

| 대상 | 권장 | 이유 |
|------|------|------|
| **신호등 LED** | YOLO 박스 + **HSV 색** (기존 `traffic_light_detector_node`) | LED 채도 높음 → 조도 흔들림에도 초록 출발용으로 쓸 만함 |
| **차선** | **YOLO-seg만** (`lane2`) | 페인트는 반사·필름·화이트밸런스에 민감 → HSV 차선 비권장 |

적불 정지가 없는 간략 미션이면, 초록 확정 후 출발만 HSV/검출기를 쓰면 된다.

---

## 2. Kingo / 공개 가중치 → 우리 카메라 (도메인 갭)

Kingo·TeamOP 계열은 **같은 화학관 트랙·같은 클래스**라 드롭인 가치가 크다. 다만:

| 요인 | 예상 |
|------|------|
| 트랙·페인트·스키마 | 동일 → 세그가 **아예 안 나오는** 경우는 드묾 |
| 카메라 높이/피치 | 다르면 마스크는 잡혀도 **중심점 편향** (BEV/ROI와 어긋남) |
| 노출·색온도·반투명 필름 | 대비↓ → 마스크 얇아짐/끊김 → `threshold`·저속으로 상당 부분 흡수 |

**실무:** `teamop_best.pt`로 정지 검출 → 저속 1바퀴. 크게 깨지면 Kingo fine-tune + 커튼 조건 수십 장. 제어([lowspeed-tuning](lowspeed-tuning.md))로 메울 갭이 “인지 완전 실패”보다 큼.

F23(`lane-center` 등)은 공식 `lane_info_extractor`와 **비호환** → 드롭인 금지([external-references](external-references.md)).

---

## 3. 내일 테스트 순서 (`weights/`)

경로 예 (실차 `~/ros2_ws`):

```text
~/ros2_ws/src/camera_perception_pkg/camera_perception_pkg/weights/
```

| 순위 | 파일 | 클래스 확인 | 비고 |
|:---:|------|-------------|------|
| 1 | `teamop_best.pt` | `lane2`, `traffic_light` | **1순위** |
| 2 | `youngsangc_best.pt` | 동일 | |
| 3 | `1taekim_best.pt` | 동일 | 실패 시 `1taekim_ti_best.pt` |
| 4 | `cms1575_best.pt` | 동일 | m-seg ~52MB, 느릴 수 있음 |
| 5 | `hlhl_best.pt` / `hlhl_best_new.pt` | 약함 | 백업 테스트 |
| — | `hlhl_traffic_light.pt` | 신호 전용 | 단일 멀티클래스 노드와 별개 · 참고만 |

```bash
W=$HOME/ros2_ws/src/camera_perception_pkg/camera_perception_pkg/weights

ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt device:=cuda:0 drive_speed:=50

# 교체 예
# model:=$W/youngsangc_best.pt
# model:=$W/1taekim_best.pt
# threshold:=0.3   # 미검출 많을 때
```

### 정지 상태 통과 기준

```bash
ros2 topic hz /detections
ros2 topic echo /detections --once
ros2 topic echo /yolov8_lane_info --once
```

- [ ] `/detections`에 `lane2` 마스크
- [ ] `/yolov8_lane_info`에 타겟점
- [ ] 실패 시 다음 순위 `.pt`로 교체 (1~2개)
- [ ] 그래도 실패 → §4 Colab

---

## 4. Colab + Roboflow (백업)

| 파일 | 역할 |
|------|------|
| [`notebooks/kingo_car.ipynb`](notebooks/kingo_car.ipynb) | Roboflow → YOLO-seg 학습 → `best.pt` |
| [Kingo Car Universe](https://universe.roboflow.com/hyeyeonim-r19sp/kingo-car-1z3da) | `lane2`+`traffic_light` · **권한 필요할 수 있음** |

1. Colab에서 `kingo_car.ipynb` 연다  
2. Roboflow API 키·프로젝트는 **팀 계정으로 교체** (노트북에 박힌 키는 쓰지 말 것)  
3. `runs/segment/train/weights/best.pt` → `weights/`에 두고 §3처럼 launch

---

## 5. 자체 수집·라벨 (나중)

```bash
python3 src/data_collection/data_collection.py
```

키: `w/s` 속도 · `a/d` 조향 · `c`/`v` 캡처 · `f` 종료  
파라미터: [setup-and-params.md](../04-dataset/setup-and-params.md)

---

## 6. 노드·launch 메모

[`yolov8_node.py`](../../src/camera_perception_pkg/camera_perception_pkg/yolov8_node.py) 기본값은 `yolov8m.pt`(스텁).  
실주행은 항상 `model:=…/weights/….pt`로 덮어쓴다.

```bash
ros2 launch launch_pkg main.launch.py model:=$W/teamop_best.pt device:=cuda:0 drive_speed:=50
ros2 launch launch_pkg main.launch.py model:=$W/teamop_best.pt device:=cuda:0 threshold:=0.4
```

---

## 7. 체크리스트 (내일)

- [ ] `teamop_best.pt` + `cuda:0` launch
- [ ] 정지 상태에서 `lane2` 검출
- [ ] 실패 시 youngsangc → 1taekim → cms 순 교체
- [ ] 저속 주행 ([lowspeed-tuning](lowspeed-tuning.md))
- [ ] 최후: `kingo_car.ipynb` 재학습
