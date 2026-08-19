# H-모빌리티 오프라인 교육 문서 (14팀)

교육 기간: **2026. 8. 12 – 2026. 8. 14**  
원본 슬라이드: [`assets/2026_H-모빌리티_오프라인교육자료_ver10.pdf`](assets/2026_H-모빌리티_오프라인교육자료_ver10.pdf) (156p)  
주행 평가 규정: [`assets/H-모빌리티 클래스 자율주행 심화과정 주행 평가 규정집_ver3.3.pdf`](assets/H-모빌리티%20클래스%20자율주행%20심화과정%20주행%20평가%20규정집_ver3.3.pdf) (ver3.3)  
팀: **14팀** (신현지, 설하원, 안승현, 박성환) · 레포: [ahnsh03/2026-HMAAC](https://github.com/ahnsh03/2026-HMAAC)

교육장에서는 `~/ros2_ws`로 클론하지만, 이 워크스페이스 경로는  
`H-Mobility-Autonomous-Advanced-Course/` 입니다. 명령어의 `~/ros2_ws`는 실차 노트북 기준 경로로 읽으면 됩니다.

## PDF Index ↔ 문서 매핑

| Index | PDF 페이지 | 문서 폴더 |
|:---:|---|---|
| (프롤로그) | p.1–8 | [`00-overview/`](00-overview/) |
| Ⅰ 부품 배부 | p.9–18 | [`01-parts-distribution/`](01-parts-distribution/) |
| Ⅱ 개발환경 구축 | p.19–37 | [`02-dev-setup/`](02-dev-setup/) |
| Ⅲ 하드웨어 | p.38–120 | [`03-hardware/`](03-hardware/) |
| Ⅳ 데이터셋 수집 | p.121–141 | [`04-dataset/`](04-dataset/) |
| Ⅴ ROS2 실습 | p.142–155 | [`05-ros2/`](05-ros2/) |
| Ⅵ 최종평가 룰미팅 | 교육PDF p.156(표지만) → **규정집 ver3.3** | [`06-final-eval/`](06-final-eval/) |
| (팀 운영) | — | [`team/`](team/) |

## 문서 트리

```text
docs/
  README.md
  common-commands.md               # 자주 쓰는 명령 · 시리얼 권한 · chmod 설명
  assets/                          # 원본 PDF · 배너
  00-overview/
  01-parts-distribution/
  02-dev-setup/
  03-hardware/
  04-dataset/
  05-ros2/
  06-final-eval/
  team/                            # 14팀 실차 가이드
    repo-structure-and-realcar-guide.md
    tomorrow-prep.md · hw-boot.md
    yolo-weights.md · teamop-vs-team14.md · controller-tuning.md
    wait-green.md · tl-hsv-tuning.md
    external-references.md · lowspeed-tuning.md
    debug-and-incremental-test.md
    launch-args.md
    notebooks/kingo_car.ipynb
    cheat-sheet.md
    archive/            # 폐기 브랜치 차이분 백업
```

## 작성 원칙

- 슬라이드 UI·조립 사진은 PDF를 보고, 여기에는 **절차·명령·핀맵·체크·주의**만 둔다.
- 각 문서 상단에 `출처: PDF p.XX–YY`를 적는다.
- 코드 경로·파라미터명은 레포의 `src/`와 맞춘다.

## 빠른 링크 (실차 재개)

- [자주 쓰는 명령어](common-commands.md)
- [레포 구조 · 실차 단계별 가이드](team/repo-structure-and-realcar-guide.md)
- [내일 실차 재개 체크리스트](team/tomorrow-prep.md)
- [HW 부팅 (장치·시리얼·SMPS)](team/hw-boot.md)
- [YOLO 가중치 적용](team/yolo-weights.md)
- [가중치 폴더 · 자동 선택 순서](../weights/README.md)
- [teamop vs team14 실차 분석](team/teamop-vs-team14.md)
- [제어기 튜닝 아이디어](team/controller-tuning.md)
- [폐기 브랜치 백업 (newmp · TEAMMODE)](team/archive/README.md)
- [초록 출발 최소 설계](team/wait-green.md)
- [신호등 HSV 튜닝 (13일)](team/tl-hsv-tuning.md)
- [소단위 디버그 · 시각화 · 로깅](team/debug-and-incremental-test.md)
- [Launch 인자 (`이름:=값`)](team/launch-args.md)
- [공개 참고 레포 · 자료](team/external-references.md)
- [저속 튜닝 · 미션](team/lowspeed-tuning.md)
- [명령/핀/키맵 치트시트](team/cheat-sheet.md)
- [차량 기록 시트](03-hardware/vehicle-record-sheet.md)
- [전원 배선·안전](03-hardware/power-wiring.md)
- [주행 평가 규정 인덱스](06-final-eval/rules.md)
- [평가 개발·검차 체크리스트](06-final-eval/dev-checklist.md)
- [페널티표](06-final-eval/penalties.md)
- [조교 구두 미션 (가규정)](06-final-eval/verbal-briefing.md)
- [미션 전략 · 정지 퓨전](06-final-eval/mission-strategy.md)
- [로깅 · 실험 준비](06-final-eval/logging-and-experiments.md)

## 저장소 브랜치 · 태그

교육 중에는 문서용 `2026`과 실차 검증용 `race`를 따로 클론해 썼지만, 2026-08-19에 **`main` 하나로 합쳤다.**

| ref | 무엇 |
|---|---|
| **`main`** | 유일한 브랜치. 문서 + 실차 검증 코드 |
| `race-final-2026-08-14` | 대회 주행에 실제로 쓴 `race` 최종본 (`8c09832`) 박제 |
| `backup/pre-race-merge-2026` | 병합 직전 `2026` 끝. 정리된 디버그 노드 3개가 여기 있다 |
| `backup/2026-team14` | 문서 전용 브랜치였음 (`launch-args.md`는 `main`에 병합됨) |
| `backup/newmp` · `backup/TEAMMODE` | 팀원 제어기 시도. 실차 미검증 — [team/archive/](team/archive/README.md) |

```bash
git clone https://github.com/ahnsh03/2026-HMAAC.git ~/ros2_ws   # main
git show race-final-2026-08-14                                   # 대회 당시 상태
git checkout -b look backup/pre-race-merge-2026                  # 정리된 노드 꺼내기
```

`main`의 코드는 `race-final-2026-08-14`의 `src/`와 **바이트 단위로 동일하다.** 병합 시 문서·`tools/`만 얹었다.
