# YOLO 가중치 — Course `weights/` 드롭인 → (필요 시) Colab·Roboflow

목적: 실차에 차선(`lane2`)·신호등(`traffic_light`)이 잡히게 한다.  
시뮬 `sim.pt`는 쓰지 않는다.

관련: [teamop-vs-team14.md](teamop-vs-team14.md) · [tl-hsv-tuning.md](tl-hsv-tuning.md) · [controller-tuning.md](controller-tuning.md) · [external-references.md](external-references.md) · [weights/README.md](../../weights/README.md) · [repo-structure-and-realcar-guide.md](repo-structure-and-realcar-guide.md) · [lowspeed-tuning.md](lowspeed-tuning.md)

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
| **이미 학습된 가중치** | **Kingo만 학습한 쪽은 `team14_best.pt`** (클래스 `box`/`undefined` 오염, 실차 `~/ros2_ws/best.pt`). `teamop_best.pt`는 `H_merge_all-1` 병합본이라 우리 차에서 더 낫다. **`best_psh.pt`**는 팀원 YOLO11s-seg(2026-08-13). 상세: [teamop-vs-team14.md](teamop-vs-team14.md) · §2.1–2.3 |
| 지금 이 WSL에서 재학습 | GPU/NVML 차단 · ultralytics 미설치 · Roboflow 403 → **지금 당장 새 `.pt` 생성은 불가** |
| Colab에서 다시 학습 | 가능. `model=yolov8s-seg.pt`(스크래치) 또는 `model=teamop_best.pt`(파인튜닝) |
| 파인튜닝에 Kingo 쓰기 | **가능·권장**. 드롭인이 커튼/카메라각에서 약하면 Kingo(+현장 소수 장)로 `teamop_best.pt`를 추가 epoch |

정리: Kingo는 “아직 아무도 학습 안 한 raw”가 아니라 **라벨드 학습셋**. 그 순수 학습본에 가까운 것은 `team14`이고, **주행 기본은 `teamop`**. `best_psh`는 차선은 좋지만 신호등이 약하고, `best_psh_v2`는 차선이 없어 주행 금지 — §3.1.

### 지금 Colab으로 갈 필요 있나? (결론)

| 질문 | 답 |
|------|-----|
| Kingo로 다시 학습해서 가져가야 하나? | **아니요.** `team14_best.pt`가 이미 Kingo-Car-1 재학습본이다. 실차 주행 기본은 `teamop`. `best_psh`는 차선 A/B용이고 신호등이 약하다 |
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

**실무:** 주행 기본은 `teamop` (§3). `best_psh`는 차선만 볼 때 A/B. IPM은 `.pt`마다 다시 맞추지 말 것. `team14`는 파이프라인 확인만.

F23(`lane-center` 등)은 공식 `lane_info_extractor`와 **비호환** → 드롭인 금지([external-references](external-references.md)).

---

## 2.1 팀 학습본 `team14_best.pt` (실차 `best.pt`)

실차 워크스페이스 루트 `~/ros2_ws/best.pt`를 14팀 학습본으로 보고, Course `weights/team14_best.pt`로 복사했다 (MD5 `096835a4…`, 22.75 MB). 공개 드롭인·`best_psh`와 **바이트 단위로 일치하지 않음**.

체크포인트(`ultralytics 8.4.105`, 날짜 2026-07-25):

| | 값 |
|--|----|
| 시작 가중치 | `yolov8s-seg.pt` (s-seg, ~11.8M) |
| 데이터 | `/content/Kingo-Car-1/data.yaml` — Colab + **Roboflow Kingo Car v1** export |
| 학습 | 10 epoch, batch 16, imgsz 640, run name `train-3` |
| 클래스 | `0 box` · `1 lane2` · `2 traffic_light` · `3 undefined` |

**Kaggle이 아님.** 문서의 [kingo-car-1z3da](https://universe.roboflow.com/hyeyeonim-r19sp/kingo-car-1z3da) / Colab `Kingo-Car-1`과 맞다. Kaggle 시뮬 이미지([skkuhhk/…](https://www.kaggle.com/datasets/skkuhhk/ros2-autonomous-vehicle-simulation))는 라벨 없는 다른 셋이다.

같은 형상(YOLOv8s-seg)끼리, 클래스 헤드(nc가 달라 shape이 다른 6개 텐서)를 빼고 겹치는 가중치 코사인 유사도. **`best_psh`(YOLO11s-seg)는 형상이 달라 이 표에 넣지 않음.**

| 비교 대상 | 학습 데이터 | nc / 이름 | 전체 | backbone | head(동일 shape) |
|-----------|-------------|-----------|-----:|---------:|-----------------:|
| **1taekim_ti_best** | **같은** `/content/Kingo-Car-1/data.yaml`, 10ep | 2 `lane2`,`traffic_light` | 0.91 | 0.88 | 0.98 |
| hlhl_best | YAD_HL-FMA-2025… | 2 `lane`,`road` (**비호환**) | 0.86 | 0.83 | 0.93 |
| 1taekim_best | `data.yaml`, 20ep | 2 `lane2`,`traffic_light` | 0.76 | 0.73 | 0.85 |
| teamop_best | `H_merge_all-1`, 10ep | 3 `lane2`,`object`,`traffic_light` | 0.63 | 0.59 | 0.73 |
| youngsangc_best | `Kingo-Car-4`, 100ep | 2 `lane2`,`traffic_light` | 0.46 | 0.44 | 0.54 |

정리:

- **가장 가까운 기존 파일은 `1taekim_ti_best.pt`.** 같은 Kingo-Car-1 경로·같은 10 epoch 레시피. 그래도 동일 파일이 아니고, 클래스 헤드만 `4` vs `2`로 갈라진다 (`model.22.cv3.*.2` weight shape `(4,128,1,1)` vs `(2,128,1,1)`).
- `teamop_best`는 **다른 데이터셋(`H_merge_all-1`)** 이라 유사도가 낮다. “Kingo를 다시 학습하면 teamop와 거의 같다”는 가정이 이 파일에는 안 맞음.
- extractor/`traffic_light_detector`는 **이름**(`lane2`, `traffic_light`)으로 필터하므로 추가 클래스 `box`/`undefined`는 무시된다. 인덱스 0을 차선으로 가정하지 말 것 (`0`은 `box`).
- **주행에는 쓰지 않는다.** 파이프라인이 도는지 한 번 확인할 때만. 주행 기본은 `teamop` (§3).

---

## 2.2 팀원 학습본 `best_psh.pt`

실차 `~/ros2_ws/weights/best_psh.pt`를 Course `weights/best_psh.pt`로 복사했다 (MD5 `a27b5a25…`, 19.55 MB). `team14_best`·공개 드롭인과 **바이트·아키텍처 모두 다름**.

체크포인트(`ultralytics 8.4.118`, 날짜 2026-08-13T02:07:19Z, Colab+Drive `YOLO_Results` / `train-3`):

| | 값 |
|--|----|
| 시작 가중치 | **`yolo11s-seg.pt`** (`yolo11s-seg.yaml`, scale s, ~10.1M 파라미터). **YOLOv8s-seg가 아님** |
| 데이터 | `/content/dataset/data.yaml` — Colab 일반 경로. **셋 이름(Kingo / 자체 수집 여부)은 ckpt에 없음** |
| 학습 | `epochs=100`, `patience=10` → 로그상 **56 epoch**에서 조기종료. batch 32, imgsz 640, dropout 0.1 |
| 클래스 | `0 lane2` · `1 traffic_light` — extractor·신호 검출기와 **이름 완전 일치** (인덱스 0이 차선) |
| 자체 val | mAP50(M) 0.993 · mAP50-95(M) 0.902 · fitness 1.816 — **자기 데이터 val**. 다른 `.pt`와 숫자 비교 금지 |

노드 호환:

- `yolov8_node`는 `ultralytics.YOLO(path)`로 로드한다. YOLO11-seg도 **이름만 맞으면** `lane2`/`traffic_light` 필터가 동작한다.
- **ultralytics ≥ 8.3** 필요. 실차가 8.0.x면 로드 실패 → 그 경우 이 파일은 건너뛰고 v8 후보만.
- v8s와 텐서 형상이 달라 team14와 **코사인 유사도 비교는 무의미**.
- 실차에서는 **차선은 좋지만 신호등이 약하다.** 그래서 주행 기본이 아니다. 차선만 볼 때 A/B. 신호만 따로 보려면 §3.1 `best_psh_v2`(차선 없음 · 주행 금지).

---

## 2.3 전 파일 라벨·레시피 일람

extractor는 **클래스 이름 문자열**(`lane2`, `traffic_light`)로 필터한다. 인덱스가 달라도 이름이 맞으면 된다. `0`을 차선으로 가정하지 말 것 (`team14`의 `0`은 `box`).

자체 val mAP는 데이터셋이 달라 **순위 근거로 쓰지 않는다.**

| 파일 | 아키텍처 | 학습 라벨 (index → name) | `train_args.data` | ep / batch | 자체 mAP50(M) | Course 차선 |
|------|----------|--------------------------|-------------------|------------|---------------|-------------|
| `team14_best.pt` | yolov8s-seg | 0 `box`, 1 `lane2`, 2 `traffic_light`, 3 `undefined` | `/content/Kingo-Car-1/data.yaml` | 10 / 16 | 0.994 | O (이름 필터) |
| `best_psh.pt` | **yolo11s-seg** | 0 `lane2`, 1 `traffic_light` | `/content/dataset/data.yaml` (셋명 미기재) | 100계획·**56실제** / 32 | 0.993 | O · ultralytics≥8.3 |
| `teamop_best.pt` | yolov8s-seg | 0 `lane2`, 1 `object`, 2 `traffic_light` | `/content/H_merge_all-1/data.yaml` | 10 / 16 | 0.991 | O |
| `1taekim_ti_best.pt` | yolov8s-seg | 0 `lane2`, 1 `traffic_light` | `/content/Kingo-Car-1/data.yaml` | 10 / 16 | 0.951 | O · team14와 최근접 |
| `1taekim_best.pt` | yolov8s-seg | 0 `lane2`, 1 `traffic_light` | `data.yaml` | 20 / 16 | 0.987 | O |
| `youngsangc_best.pt` | yolov8s-seg | 0 `lane2`, 1 `traffic_light` | `/content/Kingo-Car-4/data.yaml` | 100 / 40 | 0.986 | O |
| `cms1575_best.pt` | yolov8m-seg ~52MB | 0 `lane1`, 1 `lane1_car`, 2 `lane2`, 3 `lane2_car`, 4 `traffic_light` | `/content/자캡디ver1-16/data.yaml` | 100 / 32 | 0.988 | O (느릴 수 있음) |
| `hlhl_best.pt` | yolov8s-seg | 0 `lane`, 1 `road` | `YAD_HL-FMA-2025-…` | 10 / 16 | 0.895 | **X** (`lane2` 없음) |
| `hlhl_best_new.pt` | yolov8n-seg | 0 `lane` | `data.yaml` | 100 / 16 | 0.495 | **X** |
| `hlhl_traffic_light.pt` | yolov8s **detect** | `Green`/`Left`/`Red`/`Speed_Sign`/`Yellow` | `original-korean-traffic-light-1` | 10 / 16 | (박스만) | 신호 전용 · 단일 세그 노드와 비호환 |
| `best_psh_v2.pt` | (race `weights/`) | **`Traffic`만** | `/content/Traffic-Dataset-2` | — | — | **X 주행 금지** §3.1 |

---

## 3. 테스트 순서 (`weights/`) — 왜 이 순위인가

경로 예:

```text
# Course / 이 문서 트리
weights/

# 실차 race 워크스페이스
~/ros2_ws/weights/          # best_psh.pt · best_psh_v2.pt
~/ros2_ws/best.pt           # = team14_best.pt
```

### 우선순위 근거 (val mAP로 줄 세우지 말 것)

1. **호환이 먼저다.** `lane2`+`traffic_light` 이름이 있는 파일만 본선. HLHL·`best_psh_v2`는 차선 드롭인 금지.
2. **주행 기본은 차선과 신호등이 같이 되는 파일.** `teamop`. `best_psh`는 차선만, `best_psh_v2`는 신호등만이라 단독 주행 드롭인이 아니다. `team14`는 주행에 넣지 않는다.
3. **파이프라인만 의심되면** 실차 루트 `team14`/`best.pt`로 “노드가 도는지” 한 번 확인.
4. **정보량이 큰 파일.** 같은 Kingo-Car-1 복제(`1taekim_ti`)보다 다른 셋·다른 아키텍처가 A/B 가치가 크다.
5. **무거운 모델은 마지막.** `cms1575` m-seg는 RTX 3050에서 지연 리스크.
6. **IPM은 `.pt`와 독립.** 카메라 이미지로 한 번 맞춘 `src_*`를 모든 가중치에 재사용.

| 순위 | 파일 | 클래스 | 이 순위로 둔 이유 |
|:---:|------|--------|-------------------|
| **1** | `teamop_best.pt` | +`object` | **주행 기본.** 차선+신호등. `H_merge_all-1` |
| **2** | `best_psh.pt` | `lane2`,`traffic_light` | 차선 A/B. **신호등 약함.** YOLO11 로드 실패면 skip |
| — | `best_psh_v2.pt` | **`Traffic`만** | 신호등은 나아지나 **차선 0%.** 주행 금지 §3.1 |
| — | `team14_best.pt` | `box`,`lane2`,… | 파이프라인 확인만. Kingo-only + 클래스 오염 |
| 3 | `youngsangc_best.pt` | 2클래스 | **Kingo-Car-4** + 100ep |
| 4 | `1taekim_ti_best.pt` | 2클래스 | team14와 **같은 Kingo-Car-1**. 정보량 작음 |
| 5 | `1taekim_best.pt` | 2클래스 | conf 낮음·마스크 번짐. 백업 |
| 6 | `cms1575_best.pt` | +`lane1`/`*_car` | m-seg ~52MB, 느릴 수 있음 |
| — | `hlhl_*` | `lane`/`road` 또는 신호 색 | **본선 금지** |

시간 없으면 **`teamop`만**. 차선만 더 보고 싶으면 `best_psh`를 켠다. `best_psh_v2`는 `model:=`에 넣지 말 것.

```bash
W=$HOME/ros2_ws/weights

ros2 launch launch_pkg main.launch.py \
  model:=$W/teamop_best.pt

# 차선만 A/B
# model:=$W/best_psh.pt
# threshold:=0.3   # 미검출 많을 때
```

모터 OFF 인지 A/B는 `perception_debug.launch.py`에 같은 `model:=`를 넣는다.

제어까지 같이 볼 때: [controller-tuning.md](controller-tuning.md). team14를 다시 넣지 말 것.

### 3.1 `best_psh_v2.pt` — 신호등만 좋아지고 차선은 없음

race `f3db687`에 파일은 올렸다. **`model:=` 로 바꾸지 말 것.**

| | `best_psh.pt` | `best_psh_v2.pt` |
|--|---------------|------------------|
| names | `lane2`, `traffic_light` | **`Traffic`만** |
| 학습셋 (ckpt) | 2클래스 | `/content/Traffic-Dataset-2` |
| lane2 검출 (200장, conf=0.5) | **98.5%** (3 miss) | **0%** |
| TL 박스 (이름 리맵) | `traffic_light` 25장 | `Traffic` **49장** (v1 25장 전부 포함, +24) |
| 히트 시 평균 conf | 0.77 | 0.90 |

같은 200장에서 **teamop** 은 `traffic_light` 44장(conf 0.85). 포함 관계: **psh ⊂ teamop ⊂ v2**. teamop이 잡은 44장은 v2가 전부 다시 잡고(+5). 파이프라인이 `traffic_light`만 보면 지금 드롭인 최다 박스는 여전히 teamop.

파이프라인은 `lane2` / `traffic_light` 문자열로 고른다. v2를 넣으면 `/yolov8_lane_info`와 HSV 입력이 둘 다 끊긴다. 오프라인으로 `Traffic`을 세면 신호등 리콜은 약 2배이고 teamop(44장)보다도 박스가 많다.

팀원에게: **`lane2` + `traffic_light` 이름을 유지한 2클래스 FT**를 달라고 할 것. 지금 v2는 보조 TL 모델 후보일 뿐 주행 가중치가 아니다.

### 정지 상태 통과 기준

```bash
ros2 topic hz /detections
ros2 topic echo /detections --once
ros2 topic echo /yolov8_lane_info --once
```

- [ ] `/detections`에 `lane2` 마스크
- [ ] `/yolov8_lane_info`에 타겟점
- [ ] 실패 시 `teamop` 유지. 차선만 더 보려면 `best_psh` (YOLO11 로드 에러면 skip)
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

1. **여러 가중치를 테스트** (기본: `teamop`. 차선만 A/B: `best_psh`. team14·v2는 주행 제외)
2. **실패 지점을 기록** (아래 시트) — 어떤 `.pt`가 상대적으로 제일 나은지 고른다
3. **가장 좋았던 가중치**를 FT 시작점으로 둔다
4. 실패가 난 구간에서 **추가 로깅**(bag / `data_collection` `c`·`v`) → 라벨(`lane2`, 필요 시 `traffic_light`)
5. 그 데이터(+ 선택적으로 Kingo)로 **파인튜닝** → 새 `.pt`를 `weights/`에 넣고 재검증

드롭인이 이미 “저속 1바퀴 OK”면 FT는 미룬다. 제어([lowspeed-tuning](lowspeed-tuning.md))로 메울 수 있으면 학습보다 파라미터가 빠르다.

### 가중치 테스트 실패 기록 시트 (복사용)

시도마다 한 줄. 상세 bag 경로는 [logging-and-experiments](../06-final-eval/logging-and-experiments.md)와 맞춘다.

| 시각 | 가중치 | drive_speed / threshold | 정지 `lane2`? | 타겟점? | 신호? | 실패 지점(코너/직선/커튼/노출/각도) | bag·영상 경로 | 비고 |
|------|--------|-------------------------|---------------|---------|-------|-------------------------------------|---------------|------|
| | teamop_best | 70 / 0.5 | | | | | | **기본** |
| | best_psh | 70 / 0.5 | | | | | | 차선 A/B. 신호등 약함 |
| | team14_best | — / 0.5 | | | | | | 파이프라인 확인만 |
| | youngsangc_best | | | | | | | |
| | 1taekim_ti_best | | | | | | | team14와 같은 Kingo-Car-1 |
| | 1taekim_best | | | | | | | |
| | cms1575_best | | | | | | | m-seg 지연 확인 |

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
실주행은 항상 `model:=…/weights/….pt`로 덮어쓴다. race `main.launch.py`에는 `drive_speed`가 없을 수 있다.

```bash
ros2 launch launch_pkg main.launch.py model:=$W/teamop_best.pt
ros2 launch launch_pkg main.launch.py model:=$W/best_psh.pt
```

명령 모음: [common-commands.md §6](../common-commands.md)

---

## 8. 체크리스트 (내일)

- [ ] `teamop_best.pt` + `cuda:0` 정지 검출 (`lane2` + `traffic_light`)
- [ ] 차선만 더 볼 때 `best_psh.pt` A/B ([controller-tuning](controller-tuning.md))
- [ ] team14는 주행 스킵 (파이프라인 의심될 때만)
- [ ] `best_psh_v2`는 `model:=`에 넣지 말 것 (차선 없음)
- [ ] 저속 주행 ([lowspeed-tuning](lowspeed-tuning.md))
- [ ] 신호등 FT는 팀원 `best_psh` 쪽. 우리는 실패 코너 프레임만 라벨
