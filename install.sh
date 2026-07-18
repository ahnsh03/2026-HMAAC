#!/bin/bash
# =============================================================================
# install.sh
#   Workspace 설치 스크립트 (RTX 20 ~ 50 시리즈 공용)
#   PyTorch 를 CUDA 12.8(cu128) 빌드로 설치 → RTX 50(Blackwell / sm_120)까지 GPU 추론 지원.
#   cu128 은 sm_75(RTX 20) ~ sm_120(RTX 50) 을 모두 커버함
#     (RTX 40 = sm_89 은 같은 major 8 이라 sm_86 커널로 실행됨).
# =============================================================================

# Update package lists
sudo apt update

# Install python3-pip using apt
sudo apt install -y python3-pip

# 기존에 다른 빌드가 있을 수 있으므로 제거 후 재설치
pip uninstall -y torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# Install Python packages using pip
#  - setuptools==58.2.0 : ROS2 ament_python 빌드 호환용 (버전 고정)
#  - ultralytics        : YOLO 추론 (위에서 설치한 cu128 torch 를 그대로 사용)
#  - opencv-python      : 영상처리
#  - scipy, matplotlib  : path_planner_node 의 CubicSpline / 시각화 (numpy 기반)
#  - pyserial           : 아두이노 / RPLidar 시리얼 통신
pip install setuptools==58.2.0 ultralytics opencv-python scipy matplotlib pyserial

# 설치 검증: 아래 실행 시 본인 그래픽카드 이름(예: NVIDIA GeForce RTX 4070)이 출력되면 GPU 추론 준비 완료 (RTX 20~50 공통).
# 'CPU only' 로 나오면 GPU 인식 실패이니 NVIDIA 드라이버 설치 상태를 확인할 것.
# 본인 그래픽카드 이름은 nvidia-smi 명령어 입력을 통해 확인할 수 있음.
python3 -c "import torch; print('torch:', torch.__version__); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU only')"
