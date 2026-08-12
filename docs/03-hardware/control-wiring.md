# 제어부 연결 · 핀맵

출처: PDF p.108–117  
코드: [`src/control/driving/driving.ino`](../../src/control/driving/driving.ino)

## PC ↔ Arduino

- USB 시리얼 케이블로 연결

## 가변저항 ↔ Arduino (재확인)

| Pot | Pin |
|---|---|
| OUT | A2 |
| VCC | 5V |
| GND | GND |

## Arduino ↔ 모터드라이버 (점퍼)

| 모터 | 드라이버 IN | Arduino 핀 | `driving.ino` |
|---|---|---|---|
| 좌측 후륜 | IN1 / IN2 | **6 / 7** | `FORWARD_LEFT_1/2` |
| 우측 후륜 | IN1 / IN2 | **4 / 5** | `FORWARD_RIGHT_1/2` |
| 조향 | IN1 / IN2 | **2 / 3** | `STEERING_1/2` |

드라이버 쪽 VCC/GND(5V·GND)도 슬라이드(p.113)에 맞게 연결. 상세 사진: PDF p.115–117.

## 동작 이상 시 (데이터셋 장과 동일)

- 앞바퀴만 돌아가고 안 움직임 → **조향 핀(2/3)** 확인
- 전진/후진 반대 → **후륜 핀(4–7)** 확인·교체
