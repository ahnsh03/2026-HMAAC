# YOLO 가중치 — Course `weights/` 드롭인 → (필요 시) Colab·Roboflow

목적: 실차에 차선(`lane2`)·신호등(`traffic_light`)이 잡히게 한다.  
시뮬 `sim.pt`는 쓰지 않는다.

관련: [teamop-vs-team14.md](teamop-vs-team14.md) · [tl-hsv-tuning.md](tl-hsv-tuning.md) · [controller-tuning.md](controller-tuning.md) · [external-references.md](external-references.md) · [weights/README.md](../../src/camera_perception_pkg/camera_perception_pkg/weights/README.md) · [repo-structure-and-realcar-guide.md](repo-structure-and-realcar-guide.md) · [lowspeed-tuning.md](lowspeed-tuning.md)

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
| **이미 학습된 가중치** | **Kingo만 학습한 쪽은 `team14_best.pt`** (클래스 이름이 `box`/`undefined`로 오염). `teamop_best.pt`는 `H_merge_all-1` 병합 학습본이라 우리 차에서 더 낫다. 상세: [teamop-vs-team14.md](teamop-vs-team14.md) |
| 지금 이 WSL에서 재학습 | GPU/NVML 차단 · ultralytics 미설치 · Roboflow 403 → **지금 당장 새 `.pt` 생성은 불가** |
| Colab에서 다시 학습 | 가능. `model=yolov8s-seg.pt`(스크래치) 또는 `model=teamop_best.pt`(파인튜닝) |
| 파인튜닝에 Kingo 쓰기 | **가능·권장**. 드롭인이 커튼/카메라각에서 약하면 Kingo(+현장 소수 장)로 `teamop_best.pt`를 추가 epoch |

정리: Kingo는 “아직 아무도 학습 안 한 raw”가 아니라 **라벨드 학습셋**. 그 순수 학습본에 가까운 것은 `team14`이고, 실차에서는 병합본 `teamop`이 더 낫다. 팀원 `best_psh.pt`(yolo11s-seg)는 차선이 더 좋고 신호등이 약하다. 재학습은 팀원 TL FT + 실패 코너 프레임이 우선이다.

### 지금 Colab으로 갈 필요 있나? (결론)

| 질문 | 답 |
|------|-----|
| Kingo로 다시 학습해서 가져가야 하나? | **아니요.** Kingo 재학습은 team14에 가깝고, 실차에선 teamop·psh가 더 낫다 |
| 파인튜닝은? | **드롭인 돌려보고 안 되면** 시작. 사전 예방 파인튜닝은 시간 대비 이득 작음 |
| “알려진 정보만으로” 보완 가중치를 미리 판별? | **부분만.** 갭 후보(카메라각·커튼·노출)는 알지만, **우리 차 FOV에서 실제로 깨지는지**는 정지 검출 전에는 모름. Kingo만 추가 epoch해도 분포가 같아서 보완이 약함 |
| 언제 FT가 의미 있나? | 마스크 끊김·중심 편향이 **재현**될 때 → 그 장면(커튼/각도) **수십~수백 장** + Kingo(또는 `teamop` 초기가중치)로 FT |

명령 모음: [common-commands.md §6](../common-commands.md) · 카메라·IPM·스테이지: [debug-and-incremental-test.md](debug-and-incremental-test.md)

C920e는 **포커스만 잠그고 노출/WB는 auto** (`scripts/c920_setup.sh match_train`). 전부 픽스하지 말 것.

---

## 1. HSV vs YOLO (이번 미션)

| 대상 | 권장 | 이유 |
|------|------|------|
| **신호등 LED** | YOLO 박스 + **HSV 색** (`traffic_light_detector_node`, [13일 튜닝](tl-hsv-tuning.md)) | LED 채도 높음 → 조도 흔들림에도 초록 출발용으로 쓸 만함 |
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
| 1 | `best_psh.pt` | `lane2`, `traffic_light` | 팀원 yolo11s-seg. **차선 추종 A/B**. TL 약함 |
| 1 | `teamop_best.pt` | `lane2`, `object`, `traffic_light` | 공개 기준점. team14보다 실차에서 우위 |
| — | `team14_best.pt` | `box`, `lane2`, … | **쓰지 않음.** Kingo-only + 클래스 오염 |
| 3 | `1taekim_best.pt` | `lane2`, `traffic_light` | conf 낮음·마스크 번짐. 백업 |
| 4 | `youngsangc_best.pt` | 동일 | |
| 5 | `cms1575_best.pt` | 동일 | m-seg ~52MB, 느릴 수 있음 |
| — | `hlhl_*` | `lane` 등 | 차선 드롭인 금지 |

```bash
W=$HOME/ros2_ws/weights   # race 레포 루트. 예전 경로는 camera_perception_pkg/.../weights

ros2 launch launch_pkg main.launch.py \
  model:=$W/best_psh.pt device:=cuda:0

# 공개 기준점
# model:=$W/teamop_best.pt
# threshold:=0.3   # 미검출 많을 때
```

제어까지 같이 볼 때: [controller-tuning.md](controller-tuning.md). team14를 다시 넣지 말 것.

### 정지 상태 통과 기준

```bash
ros2 topic hz /detections
ros2 topic echo /detections --once
ros2 topic echo /yolov8_lane_info --once
```

- [ ] `/detections`에 `lane2` 마스크
- [ ] `/yolov8_lane_info`에 타겟점
- [ ] 실패 시 다음 순위 `.pt`로 교체 (1~2개)
- [ ] 그래도 실패 → §5 Colab / §4 파인튜닝

---

## 4. 파인튜닝이란 · 실패 기록 → FT

### 파인튜닝이 뭔가

**파인튜닝(fine-tuning)** = 이미 학습된 `.pt`를 **시작 가중치**로 두고, (주로 **부족한 장면**이 섞인) 데이터로 **추가 epoch**을 돌려 새 `.pt`를 얻는 것.

| | 스크래치 | 파인튜닝 |
|--|----------|----------|
| 시작 | `yolov8s-seg.pt` 등 일반 초기값 | **`teamop_best.pt` 등** 이미 `lane2`/`traffic_light`에 맞춰진 가중치 |
| 하는 일 | 처음부터 맞춤 | 기존 지식을 유지하면서 **새 조건**에 적응 |
| 데이터 | Kingo 전체만으로도 가능 | **실패 장면 프레임**이 핵심 (+ 원하면 Kingo 일부 유지) |

“폴더에 이미지 넣으면 자동 업데이트”가 아니다. Colab/로컬에서 `model.train(…)`을 한 번 더 돌려 **새 `best.pt`**를 받는다.

### 권장 워크플로 (질문에 대한 답: **맞다**)

1. **여러 가중치를 테스트** (지금: `best_psh` ↔ `teamop`. team14는 제외)
2. **실패 지점을 기록** (아래 시트) — 어떤 `.pt`가 상대적으로 제일 나은지 고른다
3. **가장 좋았던 가중치**를 FT 시작점으로 둔다
4. 실패가 난 구간에서 **추가 로깅**(bag / `data_collection` `c`·`v`) → 라벨(`lane2`, 필요 시 `traffic_light`)
5. 그 데이터(+ 선택적으로 Kingo)로 **파인튜닝** → 새 `.pt`를 `weights/`에 넣고 재검증

드롭인이 이미 “저속 1바퀴 OK”면 FT는 미룬다. 제어([lowspeed-tuning](lowspeed-tuning.md))로 메울 수 있으면 학습보다 파라미터가 빠르다.

### 가중치 테스트 실패 기록 시트 (복사용)

시도마다 한 줄. 상세 bag 경로는 [logging-and-experiments](../06-final-eval/logging-and-experiments.md)와 맞춘다.

| 시각 | 가중치 | drive_speed / threshold | 정지 `lane2`? | 타겟점? | 신호? | 실패 지점(코너/직선/커튼/노출/각도) | bag·영상 경로 | 비고 |
|------|--------|-------------------------|---------------|---------|-------|-------------------------------------|---------------|------|
| | best_psh | 70 / 0.5 | | | | | | |
| | teamop_best | 70 / 0.5 | | | | | | |

기록할 때 특히:

- **어디서** 깨지는지 (예: 커튼 구간, 급커브 진입, 역광)
- **어떻게** 깨지는지 — 마스크 없음 / 얇음·끊김 / 중심 편향(한쪽으로 쏠림) / 신호 미검출
- 같은 장면에서 **다른 `.pt`는 어떤지** (상대적으로 나은 쪽을 FT 베이스로)

### FT에 넣을 데이터

| 넣을 것 | 이유 |
|---------|------|
| 실패 장면 캡처·짧은 영상에서 뽑은 프레임 | 도메인 갭을 직접 메움 |
| (선택) Kingo 일부 | 기존 `lane2` 분포 유지, 과적합·망각 완화 |
| 넣지 말 것 | “잘 되던” 장면만 대량 추가, 라벨 없는 raw만 쌓기 |

절차 스케치: 실패 구간 녹화 → Roboflow 등에 `lane2`(세그) 라벨 → Colab에서  
`YOLO('teamop_best.pt').train(data=…, epochs=…)` → `best.pt`를 `weights/우리팀_ft.pt` 등으로 저장.

노트북 뼈대: [`notebooks/kingo_car.ipynb`](notebooks/kingo_car.ipynb) — `model=` 만 베이스 `.pt`로 바꾸면 FT.

---

## 5. Colab + Roboflow (백업)

| 파일 | 역할 |
|------|------|
| [`notebooks/kingo_car.ipynb`](notebooks/kingo_car.ipynb) | Roboflow → YOLO-seg 학습/FT → `best.pt` |
| [Kingo Car Universe](https://universe.roboflow.com/hyeyeonim-r19sp/kingo-car-1z3da) | `lane2`+`traffic_light` · **권한 필요할 수 있음** |

1. Colab에서 `kingo_car.ipynb` 연다  
2. Roboflow API 키·프로젝트는 **팀 계정으로 교체** (노트북에 박힌 키는 쓰지 말 것)  
3. **스크래치:** `yolov8s-seg.pt` / **FT:** 테스트에서 가장 나았던 `weights/*.pt`  
4. `runs/segment/train/weights/best.pt` → `weights/`에 두고 §3처럼 launch

Kingo만 다시 학습하는 것은 §0 — 이득 작음. **실패 프레임이 섞인 FT**가 목적이다.

---

## 6. 자체 수집·라벨 (나중)

```bash
python3 src/data_collection/data_collection.py
```

키: `w/s` 속도 · `a/d` 조향 · `c`/`v` 캡처 · `f` 종료  
파라미터: [setup-and-params.md](../04-dataset/setup-and-params.md)  
실패 구간만 짧게 `v`로 찍고 §4 시트에 경로를 남긴다.

---

## 7. 노드·launch 메모

[`yolov8_node.py`](../../src/camera_perception_pkg/camera_perception_pkg/yolov8_node.py) 기본값은 `yolov8m.pt`(스텁).  
실주행은 항상 `model:=…/weights/….pt`로 덮어쓴다.

```bash
ros2 launch launch_pkg main.launch.py model:=$W/teamop_best.pt device:=cuda:0 drive_speed:=50
ros2 launch launch_pkg main.launch.py model:=$W/teamop_best.pt device:=cuda:0 threshold:=0.4
```

명령 모음: [common-commands.md §6](../common-commands.md)

---

## 8. 체크리스트 (내일)

- [ ] `best_psh.pt` + `cuda:0` 정지 검출 (`lane2`)
- [ ] 같은 제어로 `teamop_best.pt` A/B ([controller-tuning](controller-tuning.md))
- [ ] team14는 스킵
- [ ] 저속 주행 ([lowspeed-tuning](lowspeed-tuning.md))
- [ ] 신호등 FT는 팀원 `best_psh` 쪽. 우리는 실패 코너 프레임만 라벨
