# 데이터셋 수집 — 준비 · 파라미터

출처: PDF p.121–138  
코드: [`src/data_collection/data_collection.py`](../../src/data_collection/data_collection.py), [`src/control/driving/driving.ino`](../../src/control/driving/driving.ino)

## 사전 조건

- [ ] 카메라 차량 고정 확인
- [ ] Arduino USB 연결
- [ ] 가변저항 좌·우 끝값 측정 완료 ([캘리브레이션](../03-hardware/potentiometer-calibration.md))

## 장치 번호

```bash
ls /dev/video*     # 노트북 웹캠 보통 0,1 → 외장 카메라 연결 후 생긴 짝수 = CAMERA_NUM
ls /dev/ttyACM*    # SERIAL_PORT (예: /dev/ttyACM0)
sudo chmod 777 /dev/ttyACM0   # 교육 PDF는 +x 표기이나 시리얼 접근은 rw 권한이 필요 → 777 또는 그룹 dialout
```

## driving.ino 반영

- 모터/가변저항 핀 번호 확인
- `resistance_most_left` / `resistance_most_right`에 측정값 입력
- `MAX_STEERING_STEP` 설정 (기본 7)
- Board Mega 2560 · Port 선택 후 **업로드**
- 시리얼 모니터는 **종료**

## data_collection.py 파라미터 (현재 레포)

```python
DATA_PATH = .../camera_perception_pkg/.../Collected_Datasets
CAMERA_NUM = 2
SERIAL_PORT = '/dev/ttyACM0'
MAX_STEERING = 7
```

**주의 (p.138):** `MAX_STEERING`(py) ↔ `MAX_STEERING_STEP`(ino) **반드시 일치**.
