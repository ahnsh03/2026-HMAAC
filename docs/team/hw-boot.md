# 내일 도착 — 하드웨어 부팅 체크 (Step A)

목적: 도착 후 **30분 안에** “장치가 살아 있는지”만 확인한다.  
전체 내일 흐름: [tomorrow-prep.md](tomorrow-prep.md) · 구조 가이드: [repo-structure-and-realcar-guide.md](repo-structure-and-realcar-guide.md)

## 1. 네트워크 · 레포

- [ ] Wi-Fi `SKKU_GUEST` · 노트북 비번 `1234`
- [ ] `cd ~/ros2_ws && git pull`
- [ ] `source /opt/ros/humble/setup.bash && source install/setup.bash`

## 2. 장치명 확인 (어제와 비교)

```bash
ls -l /dev/video*
ls -l /dev/ttyACM*
ls -l /dev/ttyUSB*
```

| 장치 | 보통 | 코드에서 고칠 곳 |
|------|------|------------------|
| 카메라 | `/dev/video0` 또는 `2` 등 | `image_publisher_node` `cam_num`, `data_collection.py` `CAMERA_NUM` |
| Arduino | `/dev/ttyACM0` | `serial_sender_node` `PORT`, `data_collection.py` `SERIAL_PORT` |
| LiDAR | `/dev/ttyUSB0` 등 | `lidar_publisher_node` 포트 |

기록: [vehicle-record-sheet.md](../03-hardware/vehicle-record-sheet.md)

- [ ] 장치명을 기록 시트와 대조했다
- [ ] 바뀌었으면 위 파라미터를 수정했다

## 3. 시리얼 권한

```bash
sudo chmod 777 /dev/ttyACM0   # 실제 장치명에 맞게
# 또는: sudo usermod -aG dialout $USER  (재로그인 필요할 수 있음)
```

- [ ] `chmod` 완료
- [ ] Arduino IDE **시리얼 모니터는 종료** (ROS와 포트 충돌 방지)

## 4. 전원 · SMPS

- [ ] 조교 확인 전 배터리 **OFF** 습관 유지
- [ ] 주행/수집 직전: SMPS **12.0V** 확인 (승압 금지)
- [ ] SMPS +V=붉/9-36V, −V=검/PGND · 모터는 OUT1/OUT2만

상세: [power-wiring.md](../03-hardware/power-wiring.md)

## 5. 가변저항 (조향 피드백)

- [ ] A2 배선 확인
- [ ] (분해·재조립했다면) 시리얼 모니터로 좌·우 끝값 재측정
- [ ] `driving.ino`의 `resistance_most_left` / `resistance_most_right`와 일치
- [ ] `MAX_STEERING_STEP`(ino) ↔ `MAX_STEERING`(py) 일치

상세: [potentiometer-calibration.md](../03-hardware/potentiometer-calibration.md)

## 6. 통과 기준 (이 단계 끝)

다음이 모두 되면 Step B(YOLO)로 넘어간다.

- [ ] `ls`로 카메라·Arduino가 보인다
- [ ] 시리얼 권한 OK, 모니터 미사용
- [ ] SMPS 12.0V 측정 가능
- [ ] 가변저항 끝값이 펌웨어와 맞다
