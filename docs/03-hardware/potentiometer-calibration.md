# 가변저항 캘리브레이션

출처: PDF p.75–88  
코드: [`src/control/check_variable_resistor/check_variable_resistor.ino`](../../src/control/check_variable_resistor/check_variable_resistor.ino)

## 배선

| 가변저항 | Arduino |
|---|---|
| OUT | **A2** |
| VCC | **5V** |
| GND | **GND** |

노트북 ↔ 아두이노: USB(파란 케이블)

## Arduino IDE

1. `File → Open` → `src/control/check_variable_resistor/*.ino`
2. `int sensorPin = A2;` 확인
3. Board: **Arduino Mega or Mega 2560**
4. Port: `/dev/ttyACM0` (또는 `ls /dev/ttyACM*` 결과)
5. Upload → `Done uploading.`
6. Serial Monitor → baud **115200** (9600이면 깨짐)

## 끝값 측정

1. 조향을 **최대 좌측** → 시리얼 값 기록 → `resistance_most_left`
2. 조향을 **최대 우측** → 시리얼 값 기록 → `resistance_most_right`
3. [`vehicle-record-sheet.md`](vehicle-record-sheet.md)에 기입

레포 `driving.ino` 기본값 예: left `938`, right `813` (차량마다 다름 — **반드시 재측정**)

## 필수 마무리

- [ ] **시리얼 모니터 종료**  
  열려 있으면 포트 점유로 ROS2/시리얼 통신 에러 (p.88)
