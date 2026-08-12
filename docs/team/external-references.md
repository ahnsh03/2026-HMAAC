# 공개 참고 레포 · 자료 (실차 노트북용)

목적: Course 팀 레포만 `git pull`한 상태에서도 **원본 URL로 클론**해 인지·제어를 참고할 수 있게 한다.  
가중치 드롭인·테스트 순서는 [yolo-weights.md](yolo-weights.md). 레포에 이미 복사된 `.pt`는 `[weights/](../../src/camera_perception_pkg/camera_perception_pkg/weights/)`.

미션 가정(간략 진행): 차선 추종 + 초록 출발 · 적불 정지·주차·차선변경·장애물 회피 없음.  
하드웨어: i7 + RTX 3050 → `device:=cuda:0`.

---

## 실차에서 참고 레포 클론

```bash
mkdir -p ~/ref && cd ~/ref
# 예: 제어·모션 참고
git clone --depth 1 https://github.com/hyeyeonIm/TeamOP.git
git clone --depth 1 https://github.com/cms1575/autonomous_vehicle_SKKU.git
git clone --depth 1 -b driving-obstacle-avoidance \
  https://github.com/x2-qp-cheese/skku-ai-autonomous-driving-2026.git f23-driving
```

작업 트리는 계속 `~/ros2_ws`(이 Course 레포)만 쓴다. `~/ref`는 읽기 전용 참고.

---



## S — 공식 스택 클래스 (`lane2` + `traffic_light`)


| 원본                                                                                  | clone                                                                                         | 활용                                                               |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| [hyeyeonIm/TeamOP](https://github.com/hyeyeonIm/TeamOP)                             | `git clone --depth 1 https://github.com/hyeyeonIm/TeamOP.git`                                 | H-모빌리티 14기 · `best.pt` · 모션/제어 → Course `weights/teamop_best.pt` |
| [youngsangc/…](https://github.com/youngsangc/H-Mobility-Autonomous-Advanced-Course) | `git clone --depth 1 https://github.com/youngsangc/H-Mobility-Autonomous-Advanced-Course.git` | 1. `lane2`/`traffic_light` → `youngsangc_best.pt`                |
| [1TAEKIM/…](https://github.com/1TAEKIM/H-Mobility-Autonomous-Advanced-Course)       | `git clone --depth 1 https://github.com/1TAEKIM/H-Mobility-Autonomous-Advanced-Course.git`    | `best.pt` + `ti_best.pt` → `1taekim_*.pt`                        |
| [gustj5092/HLHL](https://github.com/gustj5092/HLHL)                                 | `git clone --depth 1 https://github.com/gustj5092/HLHL.git`                                   | 차선·신호등 분리 가중치 → `hlhl_*.pt`                                      |


---



## A — 화학관 라운지 동일 트랙 (2026 교내 대회)


| 원본                                                                                                             | clone                                                                                                                   | 활용                                                                                                          |
| -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| [F23 driving](https://github.com/x2-qp-cheese/skku-ai-autonomous-driving-2026/tree/driving-obstacle-avoidance) | `git clone --depth 1 -b driving-obstacle-avoidance https://github.com/x2-qp-cheese/skku-ai-autonomous-driving-2026.git` | 동상 · 조향/시리얼 제어 참고. **클래스** `lane-center`**/**`lane-side` **등 → 공식** `lane_info_extractor`**와 비호환. 드롭인 금지.** |
| [F23 main](https://github.com/x2-qp-cheese/skku-ai-autonomous-driving-2026)                                    | `git clone --depth 1 https://github.com/x2-qp-cheese/skku-ai-autonomous-driving-2026.git`                               | 개요·주차 브랜치 안내                                                                                                |


---



## B — 동일 Autolab ROS2 스택 (인지+판단+제어)


| 원본                                                                                                    | clone                                                                                          | 활용                                   |
| ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------ |
| [AUTONOMOUS-PCC-Inc/ros3_ws](https://github.com/AUTONOMOUS-PCC-Inc/ros3_ws)                           | `git clone --depth 1 https://github.com/AUTONOMOUS-PCC-Inc/ros3_ws.git`                        | H-Mobility 모노레포 · ONNX/TRT · Arduino |
| [cms1575/autonomous_vehicle_SKKU](https://github.com/cms1575/autonomous_vehicle_SKKU)                 | `git clone --depth 1 https://github.com/cms1575/autonomous_vehicle_SKKU.git`                   | FSM·미션 · m-seg `cms1575_best.pt`     |
| [CCG-creator/autonomous-capstone-design](https://github.com/CCG-creator/autonomous-capstone-design)   | `git clone --depth 1 https://github.com/CCG-creator/autonomous-capstone-design.git`            | 교재 캡스톤                               |
| [LSCskywalker/automobile](https://github.com/LSCskywalker/automobile)                                 | `git clone --depth 1 https://github.com/LSCskywalker/automobile.git`                           | `best.pt` + 제어                       |
| [yunss01/dynamic_obstacle_modularization](https://github.com/yunss01/dynamic_obstacle_modularization) | `git clone --depth 1 https://github.com/yunss01/dynamic_obstacle_modularization.git`           | 동적 장애물 (이번 미션에선 낮음)                  |
| [SKKU-Auto-Drive-2024/…](https://github.com/SKKU-Auto-Drive-2024/SKKU_Autonomous_Driving_2024)        | `git clone --depth 1 https://github.com/SKKU-Auto-Drive-2024/SKKU_Autonomous_Driving_2024.git` | 캠프 계열                                |
| [2021145074-maker/yax_jeju](https://github.com/2021145074-maker/yax_jeju)                             | `git clone --depth 1 https://github.com/2021145074-maker/yax_jeju.git`                         | 차선/콘/신호 분리 가중치                       |
| [Snowor1d/2025_jacapdi2](https://github.com/Snowor1d/2025_jacapdi2)                                   | `git clone --depth 1 https://github.com/Snowor1d/2025_jacapdi2.git`                            | `best.pt` (+ sim — 실차 X)             |
| [jaeinjaein/SKKU_Autonomous_Driving_2024](https://github.com/jaeinjaein/SKKU_Autonomous_Driving_2024) | `git clone --depth 1 https://github.com/jaeinjaein/SKKU_Autonomous_Driving_2024.git`           | 제어·UI                                |


---



## 교육·규정·시뮬 (공식 인접)


| 원본                                                                                                                                          | clone                                                                                                               | 활용                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| [SKKUAutoLab/Competition-Based-Framework_ReplicationPackage](https://github.com/SKKUAutoLab/Competition-Based-Framework_ReplicationPackage) | `git clone --depth 1 https://github.com/SKKUAutoLab/Competition-Based-Framework_ReplicationPackage.git`             | 규정·워크숍·유튜브                                                                             |
| [SKKUAutoLab/ros2_autonomous_vehicle_book](https://github.com/SKKUAutoLab/ros2_autonomous_vehicle_book)                                     | `git clone --depth 1 https://github.com/SKKUAutoLab/ros2_autonomous_vehicle_book.git`                               | 교재 코드                                                                                  |
| [SKKUAutoLab/ros2_autonomous_vehicle_simulation](https://github.com/SKKUAutoLab/ros2_autonomous_vehicle_simulation)                         | `git clone --depth 1 https://github.com/SKKUAutoLab/ros2_autonomous_vehicle_simulation.git`                         | 시뮬 코드                                                                                  |
| [SKKUAutoLab/Autonomous-Driving-AI-SW-Design](https://github.com/SKKUAutoLab/Autonomous-Driving-AI-SW-Design)                               | `git clone --depth 1 https://github.com/SKKUAutoLab/Autonomous-Driving-AI-SW-Design.git`                            | 비교과 SW                                                                                 |
| [hyeyeonIm/SJSU_DATA](https://github.com/hyeyeonIm/SJSU_DATA)                                                                               | `git clone --depth 1 https://github.com/hyeyeonIm/SJSU_DATA.git`                                                    | `kingo_car.ipynb` 원본 → Course `[notebooks/kingo_car.ipynb](notebooks/kingo_car.ipynb)` |
| [thisisWooyeol/…Traffic-Light…](https://github.com/thisisWooyeol/Understanding-Traffic-Light-Signal-for-Intersection-Task)                  | `git clone --depth 1 https://github.com/thisisWooyeol/Understanding-Traffic-Light-Signal-for-Intersection-Task.git` | 신호등만                                                                                   |


---



## 레포가 아닌 자료


| 종류                 | 링크                                                                                                                                                                                                                                                                                                          | 메모                                                        |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Roboflow Kingo Car | [https://universe.roboflow.com/hyeyeonim-r19sp/kingo-car-1z3da](https://universe.roboflow.com/hyeyeonim-r19sp/kingo-car-1z3da) | 라벨드. 가중치는 학습 산출물 → 이미 `weights/teamop_best.pt` 계열. 재학습·FT: [yolo-weights.md](yolo-weights.md) |
| Kaggle 시뮬 이미지      | [https://www.kaggle.com/datasets/skkuhhk/ros2-autonomous-vehicle-simulation](https://www.kaggle.com/datasets/skkuhhk/ros2-autonomous-vehicle-simulation)                                                                                                                                                    | 라벨 없음 · 실차 조도/색감과 달라 **실차 우선순위 낮음**                       |
| HF 시뮬 가중치          | [https://huggingface.co/gogoring/simulation_ws](https://huggingface.co/gogoring/simulation_ws)                                                                                                                                                                                                              | `sim.pt` — **시뮬 전용, 실차 금지**                               |
| 제4회 SKKU AI 대회 안내  | [https://studentsuccess.oopy.io/36c91056-74bf-80e7-8edb-d074d75ca1c7](https://studentsuccess.oopy.io/36c91056-74bf-80e7-8edb-d074d75ca1c7)                                                                                                                                                                  |                                                           |
| H-모빌리티 공식 `2026`   | [https://github.com/SKKUAutoLab/H-Mobility-Autonomous-Advanced-Course/tree/2026](https://github.com/SKKUAutoLab/H-Mobility-Autonomous-Advanced-Course/tree/2026)                                                                                                                                            |                                                           |
| 제2회 SW경진대회 유튜브     | [https://www.youtube.com/watch?v=hmLsHTXk_fI](https://www.youtube.com/watch?v=hmLsHTXk_fI)                                                                                                                                                                                                                  | 2024.07.19 화학관                                            |
| Autolab 워크숍 플레이리스트 | [https://youtube.com/playlist?list=PLIyoAG_PPqRdchsJlDibNFsI55hPlu30l](https://youtube.com/playlist?list=PLIyoAG_PPqRdchsJlDibNFsI55hPlu30l)                                                                                                                                                                |                                                           |
| Autolab 캡스톤 1 / 2  | [https://www.youtube.com/playlist?list=PLIyoAG_PPqRfhqFnaGwwP4ROqpAk9VcMI](https://www.youtube.com/playlist?list=PLIyoAG_PPqRfhqFnaGwwP4ROqpAk9VcMI) · [https://www.youtube.com/playlist?list=PLIyoAG_PPqRemDN7lFsWcU-SAKQBk8Tfe](https://www.youtube.com/playlist?list=PLIyoAG_PPqRemDN7lFsWcU-SAKQBk8Tfe) |                                                           |


---



## 권장 참고 순서

1. Course `weights/` S급 드롭인 ([yolo-weights.md](yolo-weights.md))
2. 제어·모션: TeamOP · cms1575 · PCC `ros3_ws` (clone)
3. 동일 트랙 제어 감각: F23 driving (**가중치 드롭인 X**)
4. 깨지면 Kingo 재학습: `[notebooks/kingo_car.ipynb](notebooks/kingo_car.ipynb)` + Roboflow

