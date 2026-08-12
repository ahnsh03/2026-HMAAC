# 차량 기록 시트 (14팀)

출처: PDF p.86–87, p.125–126, p.136–138, p.141

실차마다 값이 다르므로 **차량/배터리 라벨 기준으로 한 장** 채운다.

## 식별

| 항목 | 값 |
|---|---|
| 조 / 팀 | 14팀 |
| 차량 라벨 | |
| 측정 일시 | |
| 측정자 | |

## 가변저항 끝값

| 항목 | 값 | 비고 |
|---|---|---|
| `resistance_most_left` (최대 좌) | | `driving.ino` |
| `resistance_most_right` (최대 우) | | `driving.ino` |
| `MAX_STEERING_STEP` / `MAX_STEERING` | 7 (기본) | **ino ↔ py 일치** |

## 장치 이름

| 항목 | 명령 | 값 |
|---|---|---|
| `SERIAL_PORT` | `ls /dev/ttyACM*` | 예: `/dev/ttyACM0` |
| `CAMERA_NUM` | `ls /dev/video*` 중 **짝수** | 예: `2` |
| LiDAR | `ls /dev/ttyUSB*` | 예: `/dev/ttyUSB0` |

## 조향 모터 선 색 (사전 확인 p.61–62)

| 위치 | 색 |
|---|---|
| 앞(조향 모터측) | |
| 뒤(연결 연장선) | |

## 메모

```
(배선 이슈, 모터 방향 반전, 핫플러그로 장치명 변경 등)
```
