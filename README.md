# H-모빌리티 클래스 자율주행 심화과정

<img src="docs/H-모빌리티_Github_banner.png" alt="자율주행 심화과정 입과를 환영합니다 — H-모빌리티 클래스 X 현대자동차" width="100%">

성균관대학교 자동화연구실의 H-모빌리티 클래스 자율주행 심화과정 실습 코드입니다.

---

## 시작하기

### 1. 개발 환경 설정 — 사전 온라인 강의 수강 (1 ~ 9번)

eX-campus의 사전 온라인 강의를 **1번부터 9번까지** 순서대로 수강하며 개발 환경 설정을 모두 마칩니다.

| 강의 | 내용 |
|:---:|---|
| 0 | H-모빌리티 클래스 자율주행 심화과정 OT |
| 1 | Ubuntu 22.04 설치 |
| 2 | 시스템 업데이트 실행 |
| 3 | Linux 기초 명령어 |
| 4 | Terminator 설치 |
| 5 | VS Code 설치 |
| 6 | ROS2 설치 |
| 7 | Arduino IDE 설치 |
| 8 | 한국어 입력 설정 |
| 9 | NVIDIA Driver 설치 |

### 2. git clone (10번)

- **`git clone`** 으로 복제하거나 (git clone 사용법은 **10번 강의**에서 설명합니다.)

> [주의]
> **시뮬레이션 과제는 하단의 repository로 이동하여 git clone하여 주시기 바랍니다.**
> 본 repository는 오프라인 교육에서 사용합니다.
- 저장소 상단의 초록색 **`Code`** 버튼을 누른 뒤 **Download ZIP** 으로 압축 파일을 받아 원하는 위치에 풉니다.

```bash
git clone https://github.com/SKKUAutoLab/H-Mobility-Autonomous-Advanced-Course.git
cd H-Mobility-Autonomous-Advanced-Course
```

### 3. 의존성 설치 — `install.sh` 실행 (10-1번)

내려받은 폴더 안에서 설치 스크립트를 실행합니다. PyTorch·ultralytics·OpenCV 등 필요한 파이썬 패키지를 한 번에 설치합니다.

```bash
bash install.sh
```

> 스크립트 끝에서 **본인 그래픽카드 이름**(예: `NVIDIA GeForce RTX 4070`)이 출력되면 GPU 사용 준비가 된 것입니다.<br>
> (`CPU only` 로 나오면 NVIDIA 드라이버 설치 상태를 확인하세요.)

### 4. 워크스페이스 빌드 — `colcon build`

```bash
source /opt/ros/humble/setup.bash   # ROS2 환경 불러오기
colcon build --symlink-install
```

### 5. 환경 적용 — `source`

빌드 결과(워크스페이스)를 현재 터미널에 적용합니다.

```bash
source install/setup.bash
```

여기까지 완료하면 실행 준비가 끝납니다. 예시:

```bash
ros2 launch launch_pkg main.launch.py
```

---

> ⚠️ 터미널을 새로 열 때마다 `source /opt/ros/humble/setup.bash` 와 `source install/setup.bash` 를 다시 실행해야 합니다.

---

<a href="https://github.com/SKKUAutoLab/H-Mobility-Autonomous-Advanced-Course-Simulation" style="display: block; width: 100%;">
  <img src="https://github.com/user-attachments/assets/934b84c8-667e-4228-be4a-d0c54dff827f" alt="H-Mobility-Autonomous-Advanced-Course-Simulation" style="display: block; width: 100%;">
</a>

<sub>본 저장소의 소스 코드는 <a href="LICENSE">GPL-3.0 License</a> 하에 공개됩니다. 교육·연구 목적으로 자유롭게 활용하실 수 있으며, 코드를 사용하거나 재배포하실 경우 성균관대학교 자동화연구실의 <i>H-모빌리티 클래스 자율주행 심화과정</i>을 출처로 밝혀 주시기 바랍니다.</sub>
