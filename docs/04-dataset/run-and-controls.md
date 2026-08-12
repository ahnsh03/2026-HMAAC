# 데이터셋 수집 — 실행 · 키 조작

출처: PDF p.139–140  
코드: [`src/data_collection/data_collection.py`](../../src/data_collection/data_collection.py)  
참고: [`command.txt`](../../command.txt)

## 실행

교육 PDF:

```bash
sudo pip install keyboard
sudo pip install pyserial
sudo python3 ~/ros2_ws/src/data_collection/data_collection.py
```

팀 레포 개선본은 rootless 키보드 브리지를 쓰므로, 권한만 맞으면 일반 사용자 실행도 가능하다:

```bash
ls /dev/ttyACM* /dev/video*
sudo chmod 777 /dev/ttyACM0
python3 src/data_collection/data_collection.py
```

## 키맵 (현재 코드 기준)

| 키 | 동작 |
|---|---|
| `w` / `s` | 속도 |
| `a` / `d` | 조향 |
| `r` | 리셋 |
| `c` | 프레임 저장 |
| `v` | 영상 녹화 토글 (팀 추가) |
| `f` | 종료 |

프리뷰 창 또는 터미널에 포커스를 두고 조작한다.

## 저장 위치

- 수집 루트: `camera_perception_pkg/.../Collected_Datasets`
- 녹화 파일은 `data_collection_path` 하위에 타임스탬프명으로 저장
