# teamop이 team14보다 나은 이유 (실차 프레임 분석)

목적: 공개 드롭인 중 **제어 튜닝의 기준 가중치**를 고정한다.  
결론부터: **`teamop_best.pt`를 쓰고, `team14_best.pt`는 쓰지 않는다.**

관련: [yolo-weights.md](yolo-weights.md) · [controller-tuning.md](controller-tuning.md) · [external-references.md](external-references.md)

날짜: 2026-08-13. 실차 수집본 `data/2026-08-12-17-14-05`(c캡처) · `data/2026-08-13-12-46-44`(v→PNG).  
추론: conf=0.5, imgsz=640, `cuda:0`. 오버레이는 워크스페이스 `data/_weight_compare/` (레포 밖).

---

## 0. 한 줄

| 가중치 | 실차에서 | 이유 |
|--------|----------|------|
| **teamop_best** | **주행 기본 1순위** | 차선+신호등. 학습셋이 병합본이고, 코너에서 lane2가 안 빠지며 conf 여유가 큼 |
| team14_best | 쓰지 말 것 | Kingo만 학습 + 클래스 이름이 공식 스키마와 다름 + 코너 미검출 |
| 1taekim_best | 백업 | 공식 2클래스이지만 conf가 0.5 근처, 마스크가 번짐 |
| **best_psh** (팀원) | **차선만 A/B** | 차선은 좋지만 **신호등이 약함** |
| **best_psh_v2** | 쓰지 말 것 | 신호등은 나아지나 **차선이 없음** |

지금 할 일: **`teamop`을 기본 `model:=`로 쓴다.** 차선만 더 볼 때 `best_psh`. team14·v2는 주행에 넣지 않는다.

---

## 1. 예전 문서가 틀렸던 점

[yolo-weights.md](yolo-weights.md) 초안에 “teamop ≈ Kingo 학습본”이라고 적어 두었다. 체크포인트 메타를 열어 보니 **반대에 가깝다.**

| | team14_best | teamop_best | 1taekim_best |
|--|-------------|-------------|--------------|
| 아키텍처 | yolov8s-seg | yolov8s-seg | yolov8s-seg |
| 학습 데이터 | **`Kingo-Car-1`** | **`H_merge_all-1`** | `data.yaml` (경로만) |
| 날짜 | 2026-07-25 | 2024-07-24 | 2024-07-23 |
| epochs | 10 | 10 | 20 |
| `names` | **`box`, `lane2`, `traffic_light`, `undefined`** | `lane2`, `object`, `traffic_light` | `lane2`, `traffic_light` |
| 자체 val mAP50-95(B) | **0.74** | 0.92 | 0.92 |
| 자체 val precision(B) | **0.80** | 0.99 | 0.94 |

자체 val은 데이터셋이 달라서 모델 간 순위로 쓰면 안 된다. 다만 team14만 localization(mAP50-95)이 유난히 낮다. Kingo val에서 박스는 대충 맞지만 마스크가 헐겁다는 뜻이다.

extractor는 `class_name == 'lane2'`만 본다. team14도 lane2는 있다. 문제는 **클래스 0이 `box`** 라는 점이다. 학습 신호가 공식 2클래스와 어긋나 있고, `undefined`까지 섞여 있다.

teamop의 `object`는 주차 차량 등에 쓰인 3번째 클래스다. extractor는 무시하므로 차선 추종은 깨지지 않는다.

---

## 2. 우리 카메라 200장 (이 숫자가 우선)

표본: 12일 c캡처를 `|steer|`로 나눔 — 직선(≤1) 40 · 커브(2–4) 40 · 코너(≥5) 40.  
13일 v녹화에서 균등 샘플 80장. 합 200.

| | 전체 검출률 | 미검출 | 코너 미검출 | 평균 max conf | 마스크 면적 |
|--|-------------|--------|-------------|---------------|-------------|
| team14 | 90% | 20 | **8 / 40** | 0.76 | 18.2% |
| **teamop** | **98%** | **4** | **0 / 40** | **0.90** | 20.1% |
| 1taekim | 84% | 32 | 8 / 40 | 0.58 | 29.2% |

- 노드 기본 `threshold=0.5`. 1taekim 평균 conf 0.58이면 코너에서 쉽게 끊긴다.
- 1taekim 면적 29%는 “더 잘 채운다”가 아니라 **초록 잔디·노면까지 번진 과대 마스크**다. 중심점이 흔들린다.
- teamop은 같은 코너 40장에서 lane2가 한 장도 안 빠졌고, conf가 0.94라 임계값 여유가 있다.
- 세 모델 모두 **같은 첫 코너·S자에서 마스크가 얇아지거나 끊긴다.** 그래서 추가 학습은 여전히 필요하다. 다만 공개 가중치 중 시작점은 teamop이다.

오버레이에서 본 패턴:

- team14: 코너에서 `NO MASK`, S자에서 아스팔트를 lane2로 칠하는 장면이 있음.
- teamop: 초록 주행면을 가장 연속적으로 채움. 공식 `lane2` 의미(흰 페인트 한 줄이 아님)와 맞음.
- 1taekim: 블록처럼 거칠고 경계가 차선 밖으로 나감.

---

## 3. 왜 teamop이 우리 차에 더 맞나

1. **도메인.** Kingo만 본 team14보다, 여러 셋을 합친 `H_merge_all`이 카메라각·조명 변화에 덜 깨진다. 우리 C920e·화학관 라운지는 Kingo와 “같은 트랙”이지만 높이/피치/노출이 다르다.
2. **클래스 정렬.** extractor·신호 HSV는 `lane2` / `traffic_light`를 이름으로 찾는다. team14의 `box`/`undefined`는 학습을 희석한다.
3. **임계값 여유.** 같은 0.5에서 teamop만 코너를 놓치지 않았다. 제어기가 경로를 잃는 횟수가 줄어든다.
4. **마스크 품질.** 면적만 넓다고 좋지 않다. 1taekim처럼 번지면 `get_lane_center`가 한쪽으로 튄다. teamop은 면적 20%대에서 경계를 더 지킨다.

teamop이 “완벽”은 아니다. 첫 코너·S자는 세 모델 공통 약점이다. 그 구간은 팀원 `best_psh` 차선 FT / 우리가 고른 실패 프레임으로 메운다.

---

## 4. `best_psh` vs `teamop` (같은 200장, 2026-08-13)

둘 다 conf=0.5. psh는 yolo11s-seg라 컨테이너 ultralytics 8.2에서는 로드가 안 되고 8.3+가 필요하다. 실차에서 이미 돌았다면 노트북 버전이 충분하다.

| | teamop | best_psh |
|--|--------|----------|
| lane2 검출률 | 98.0% (미검출 4) | **98.5% (미검출 3)** |
| 코너 40장 | 100% | 100% |
| 커브 40장 | **100%** | 97.5% (1장 놓침) |
| 직선 40장 | 95% | **100%** |
| 평균 lane conf | 0.90 | 0.90 |
| 마스크 면적 | 20.1% | 18.4% (조금 더 타이트) |
| 파편(≥3덩이) | 25장 | 33장 |
| 서로 IoU | — | **0.88** |
| psh만 lane / op만 lane | 3 / 2 | |
| TL 박스 있는 프레임 | **44 (22%)** | 25 (12.5%) |
| 상대만 잡은 TL | 19 | **0** |

해석:

- **차선 검출률은 사실상 동률**이다. 체감으로 psh가 나은 이유는 곡선에서 마스크가 더 진하고 끊김이 적어 보이기 때문이다. 숫자는 면적이 약간 작고(잔디로 덜 번짐) 조각은 조금 더 많다.
- 사람·가장자리 장면에서는 psh가 주행면 밖으로 큰 삼각형을 칠한 컷이 있다. “항상 더 안전”은 아니다.
- **신호등 박스는 teamop이 명확히 우위**다. psh가 teamop을 이긴 TL 프레임은 0이다. 출발 게이트([wait-green.md](wait-green.md))는 출발선 echo로 박스가 나오는 쪽을 쓴다.

제어 A/B는 그대로 유효하다. 차선만 보면 둘 다 쓸 수 있고, 출발 게이트만 보면 당분간 teamop이 더 안전하다.

## 4b. 팀원 `best_psh.pt` 메타

체크포인트 메타 (2026-08-13):

| | best_psh |
|--|----------|
| 아키텍처 | **yolo11s-seg** (v8 아님) |
| 클래스 | `lane2`, `traffic_light` (공식 2클래스) |
| 학습 | `/content/dataset/data.yaml`, epochs≈100 |
| 실차 체감 | **차선 최고**, **신호등 약함** |
| 다음 | 팀원이 신호등 추가학습 |

`yolov8_node`는 ultralytics `YOLO()`라 11-seg도 로드된다. 실차 ultralytics가 너무 오래되면(8.2 이하) 실패할 수 있다. 그때는 `python3 -c "import ultralytics; print(ultralytics.__version__)"` 확인.

제어 튜닝 동안의 역할:

| 가중치 | 쓰는 이유 |
|--------|-----------|
| `best_psh.pt` | 차선이 제일 잘 붙을 때 조향·속도 노브를 본다 |
| `teamop_best.pt` | 공개 기준점. 차선이 조금 덜 붙어 있을 때 제어가 얼마나 버티는지 본다 |
| team14 | 넣지 않음 |

둘 다 같은 코너에서 이탈하면 **인지 문제가 아니라 제어**다. psh만 통과하고 teamop만 이탈하면 마스크 품질 차이다.

출발 게이트는 [wait-green.md](wait-green.md). psh의 TL 약점은 출발선 echo로 확인하고, 박스만 안 나오면 게이트 검증은 teamop으로 한다.

---

## 5. 파인튜닝 / Roboflow (팀원 TL 작업과 겹치지 않게)

- 공개 가중치를 우리가 또 FT할 필요는 없다. 차선은 psh가 앞서고, TL은 팀원이 psh에 추가학습한다.
- 우리가 라벨할 거면 **실패 코너·S자만**. `lane2`는 흰 선이 아니라 **초록 주행면 전체** (Kingo/teamop과 동일).
- teamop으로 FT할 때만 클래스 순서를 `0=lane2, 1=object, 2=traffic_light`로 맞춘다. psh는 이미 `0=lane2, 1=traffic_light`이므로 **teamop 스키마를 psh에 그대로 넣지 말 것.**

---

## 6. 실차 스왑 명령

race 작업트리 기준 가중치는 레포 루트 `weights/`.

```bash
W=~/ros2_ws/weights   # 또는 레포 루트 weights/

# 주행 기본
ros2 launch launch_pkg perception_debug.launch.py \
  model:=$W/teamop_best.pt device:=cuda:0

# 차선만 A/B (신호등 약함)
ros2 launch launch_pkg perception_debug.launch.py \
  model:=$W/best_psh.pt device:=cuda:0
```

폐루프는 [controller-tuning.md](controller-tuning.md). team14는 위 명령에 넣지 않는다.
