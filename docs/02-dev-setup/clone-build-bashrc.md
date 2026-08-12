# Clone · Install · Build · bashrc

출처: PDF p.31–37  
관련: 레포 루트 `install.sh`, `README.md`

## 1. 저장소 클론

교육 슬라이드 기본 URL (브랜치 `2026`):

```text
https://github.com/SKKUAutoLab/H-Mobility-Autonomous-Advanced-Course/tree/2026
```

```bash
cd ~
git clone <HTTPS_URL> ros2_ws
ls ~/
cd ~/ros2_ws
```

**14팀 실차/개발용**은 팀 레포를 사용한다:

```bash
git clone -b 2026 https://github.com/ahnsh03/2026-HMAAC.git ros2_ws
# 또는 이미 클론된 H-Mobility-Autonomous-Advanced-Course 디렉터리 사용
```

터미널 붙여넣기: `Ctrl+Shift+V` / 복사: `Ctrl+Shift+C`

## 2. 의존성 설치

```bash
cd ~/ros2_ws   # 또는 이 워크스페이스 루트
chmod +x install.sh
./install.sh
```

스크립트 끝에 GPU 이름(예: `NVIDIA GeForce RTX …`)이 보이면 OK. `CPU only`면 드라이버 확인.

## 3. 빌드

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

실패 시:

```bash
rm -rf build install log
colcon build --symlink-install
```

## 4. 환경 영구화 (bashrc)

교육 PDF 권장 (한 줄):

```bash
echo "cd ~/ros2_ws && source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

또는 분리해서:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

새 터미널마다 적용 확인:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
```

네트워크 격리(`ROS_LOCALHOST_ONLY`)는 [05-ros2/network-domain.md](../05-ros2/network-domain.md) 참고.
