# ROS 2 Humble (Ubuntu 22.04) — 오프라인/실차 실습 레포 전용 개발 이미지
#
# 호스트가 Ubuntu 26.04 (WSL2) 처럼 Humble 공식 지원 대상이 아닐 때 쓴다.
# 내용은 이 레포의 install.sh 와 src/*/package.xml 을 그대로 옮긴 것이다.
#
# 베이스가 ros:humble(ros-base) 인 이유: 이 레포의 package.xml 은 cv_bridge / rclpy /
# sensor_msgs / geometry_msgs / std_srvs 만 요구한다. Gazebo·rviz2·urdf·ros2_control 은
# 시뮬 레포 쪽 의존성이라 여기서는 desktop-full(약 +5GB)이 필요 없다.
#
#   cd docker && docker compose build && docker compose up -d
FROM ros:humble

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV QT_X11_NO_MITSHM=1
ENV ROS_DOMAIN_ID=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    nano \
    vim \
    tmux \
    psmisc \
    locales \
    udev \
    python3-pip \
    python3-dev \
    python3-colcon-common-extensions \
    python3-rosdep \
    ros-humble-cv-bridge \
    ros-humble-image-transport \
    # matplotlib 창 · cv2.imshow 프리뷰용 (실차 디버깅)
    libgl1-mesa-glx \
    libglib2.0-0 \
    python3-tk \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# install.sh 의 pip 목록.
#  - install.sh 는 cu128 torch(RTX 20~50 GPU 추론)를 깐다. 컨테이너에서도 GPU 추론을
#    하려면 compose 의 hmobility-offline 이 gpus: all 로 뜨므로 그대로 쓰면 된다.
#    GPU 없이 코드만 볼 때는 아래 TORCH_INDEX 를 cpu 로 바꿔 빌드하면 수 GB 를 아낀다:
#      docker compose build --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cpu
#  - apt 의 sympy(distutils) 와 충돌하므로 pip 쪽을 --ignore-installed 로 덮는다.
#  - colcon/ament 는 setuptools 58.x 를 요구한다 (최신 setuptools 는 strip_trailing_zero 오류).
#  - scipy 는 path_planner_node 의 CubicSpline 에 필요하다.
ARG TORCH_INDEX=https://download.pytorch.org/whl/cu128
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir --ignore-installed sympy mpmath && \
    pip3 install --no-cache-dir torch torchvision --index-url ${TORCH_INDEX} && \
    pip3 install --no-cache-dir \
      ultralytics \
      opencv-python \
      scipy \
      matplotlib \
      pyserial && \
    pip3 install --no-cache-dir "setuptools==58.2.0" "packaging==23.2"

# compose 가 레포 루트를 여기에 마운트한다
WORKDIR /root/hmobility_ws

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "[ -f /root/hmobility_ws/install/local_setup.bash ] && source /root/hmobility_ws/install/local_setup.bash" >> /root/.bashrc && \
    echo "export ROS_DOMAIN_ID=\${ROS_DOMAIN_ID:-1}" >> /root/.bashrc && \
    echo "alias MOVE='ros2 service call /go std_srvs/srv/SetBool \"{data: true}\"'" >> /root/.bashrc && \
    echo "alias STOP='ros2 service call /go std_srvs/srv/SetBool \"{data: false}\"'" >> /root/.bashrc

CMD ["bash"]
