# 신호등 HSV 튜닝 (13일 실차)

상태: **race 워킹트리에 반영.** 커밋은 아직 안 함.  
데이터: `data/2026-08-13-12-46-44/` (12:46 녹화 프레임)  
관련: [wait-green.md](wait-green.md) · [yolo-weights.md](yolo-weights.md) · [debug-and-incremental-test.md](debug-and-incremental-test.md)

---

## 결과

608장 샘플 (출발은 8프레임마다, 이후 30프레임마다) → `teamop_best.pt` conf 0.45 → **신호등 박스 258개.**

| | 교육 기본 | 튜닝 후 |
|--|-----------|---------|
| 점등 251장 (적 145 + 녹 106) | 100% | **100%** |
| 꺼진/과대박스 7장 | 전부 거짓 **Red** | 전부 **Unknown** |
| 전체 258장 | 97.3% | **100%** |
| 거짓 Green | 0 | 0 |

점등 LED는 원래도 맞았다. 인식률을 올린 지점은 **꺼진 등을 Red로 밀어 넣던 버그**다.  
`motion_planner`는 `Red`이고 `y_max < 150`이면 급정지한다. 거짓 Red는 출발 게이트·주행 중 모두 위험하다.

이 세트에 **노란 점등은 0장.**

---

## 왜 기본 HSV가 깨졌나

`get_traffic_light_color`가 ROI 전체 픽셀 비율만 보고, 세 비율이 전부 0이면

```text
max(0, 0, 0) == red_ratio  →  "Red"
```

13일 실패 7장은 전부 **좌측 끝 과대박스** (꺼진 하우징 + 창문/트러스). 유채색 LED가 거의 없다.

점등 vs 꺼짐은 범위보다 **LED 픽셀 양**으로 갈린다 (`S≥40` and `V≥70`):

| | LED 픽셀 | LED / 박스 |
|--|----------|------------|
| 점등 min | 461 | 4.1% |
| 꺼짐 max | 61 | 0.24% |

---

## 적용한 값

`traffic_light_detector_node` 범위 (OpenCV H 0–179). S/V 하한을 교육 기본 100/95에서 낮춤 — 녹 LED 후광 S p10 ≈ 50.

| | 교육 기본 | 13일 튜닝 |
|--|-----------|-----------|
| red1 | (0,100,95)–(10,255,255) | **(0,50,70)–(12,255,255)** |
| red2 | (160,100,95)–(179,255,255) | **(155,50,70)–(179,255,255)** |
| yellow | (20,100,95)–(30,255,255) | **(16,50,70)–(38,255,255)** |
| green | (40,100,95)–(90,255,255) | **(35,40,55)–(95,255,255)** |

`get_traffic_light_color` 가드:

- ROI를 이미지 안으로 클램프
- LED 마스크만 비율 계산
- LED 픽셀 **&lt; 80** 또는 박스 대비 **&lt; 1%** → `Unknown`
- 최댓값 비율 **&lt; 8%** 또는 2등과의 차 **&lt; 10%** → `Unknown`

범위만 넓히면 과대박스의 잔디/콘이 거짓 Green이 된다 (프레임 12210). 게이트가 필수다.

---

## 재현

```bash
docker run --rm --gpus all --ipc=host \
  -v /home/aim06/projects/2026-H-Mobility-Class:/work -w /work \
  hmobility-humble:cuda \
  python3 /work/data/_scripts/verify_tl_hsv.py
```

캐시된 박스만 다시 채점: `data/_scripts/rescore_tl_hsv.py`  
산출: `data/_weight_compare/tl_hsv/verify.json`

---

## 아직 안 되는 것

- **박스가 없으면 색도 없다.** 같은 영상에서 teamop TL 박스가 psh보다 많다. 출발 게이트 검증은 당분간 teamop.
- `main.launch.py`의 `traffic_light_detector_node`는 **아직 주석.**
- 조명·WB가 바뀌면 LED 게이트(80 / 1%)를 다시 재다.
- WAIT_GREEN FSM은 이 변경에 포함하지 않음 ([wait-green.md](wait-green.md)).
