# Ⅵ 주행 평가 규정 (인덱스)

출처: [규정집 ver3.3](../assets/H-모빌리티%20클래스%20자율주행%20심화과정%20주행%20평가%20규정집_ver3.3.pdf) (2026.08.11, 10p)

> **가규정 알림:** 룰 미팅 전 조교 구두 안내는  
> [verbal-briefing.md](verbal-briefing.md) · [mission-strategy.md](mission-strategy.md) · [logging-and-experiments.md](logging-and-experiments.md)  
> 에 정리되어 있다. **내일 룰미팅 확정본이 우선**한다.

오프라인 교육 PDF(ver10)의 「최종평가 룰미팅」은 표지만 있었고,  
공식 채점·트랙·페널티 문서는 **본 규정집**이 기준이다.

## 문서 목록

| 파일 | 내용 |
|---|---|
| [competition-rules.md](competition-rules.md) | Ⅰ 목적·운영·준비·채점 권한 |
| [operations.md](operations.md) | Ⅱ 기본/시간경기/기술/검차/이의 |
| [timing.md](timing.md) | Ⅲ 랩타이머·신호등 출발·최종기록 |
| [track-and-missions.md](track-and-missions.md) | Ⅳ 치수·차선·랩타이머 충돌 |
| [penalties.md](penalties.md) | Ⅴ 페널티 코드 a/b/c |
| [dev-checklist.md](dev-checklist.md) | 개발·검차 대비 체크리스트 |
| [verbal-briefing.md](verbal-briefing.md) | 조교 구두 미션 (가규정) |
| [mission-strategy.md](mission-strategy.md) | 상태머신·정지 퓨전 전략 |
| [logging-and-experiments.md](logging-and-experiments.md) | 내일 로깅·실험 체크리스트 |

## 핵심 한 장 요약

- **미션:** 2차선 · 반시계 · **2바퀴** · 신호등 초록 후 출발 · 종료 시 물체 탐지 후 정지
- **제한시간:** 4분 (초과/진행불가 = 완주 실패). 팀당 기회 1회 (+ 조건 충족 시 재출발 1회)
- **HW:** 제공 부품만 · 개조 금지 · **SMPS 12.0V** · 센서 전후 110 / 좌우 60 / 높이 75 cm
- **차선 (2차로·구두):** 왼쪽 **점선 밟기=페널티(b3)** · 오른쪽 **실선 밟기=무페널티** · **양쪽 모두 넘어가면 페널티(b1)**
- **구두 보강:** 1랩 무장애 · 도착 차량≈출발점+30cm · 랩2 종료까지 **신호등 초록** · **차량 감지 후 정지** · FOV 퓨전

상세: [dev-checklist.md](dev-checklist.md) · [verbal-briefing.md](verbal-briefing.md)
