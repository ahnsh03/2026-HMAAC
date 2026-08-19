# Docker (ROS 2 Humble)

호스트가 Ubuntu 26.04 (WSL2) 처럼 Humble 공식 지원 대상이 아닐 때, 이 레포를
컨테이너 안에서 빌드·실행하기 위한 환경이다. `install.sh` 와 `src/*/package.xml` 을
이미지에 굳혀 둔 것이라 **`install.sh` 를 컨테이너에서 다시 돌릴 필요는 없다.**

베이스는 `ros:humble`(ros-base) 이다. 이 레포는 `cv_bridge` / `rclpy` / `sensor_msgs` /
`geometry_msgs` / `std_srvs` 만 요구하고 Gazebo·rviz2·`ros2_control` 은 쓰지 않으므로
`desktop-full`(약 +5GB)을 쓰지 않는다. 시뮬은 별도 레포
([ahnsh03/2026-HMAAC-Sim](https://github.com/ahnsh03/2026-HMAAC-Sim))에 자기 Docker 환경이 있다.

## 기동

```bash
xhost +local:docker
cd docker
docker compose build        # 첫 1회
docker compose up -d
docker exec -it hmobility-offline bash
```

레포 루트가 컨테이너의 `/root/hmobility_ws` 로 마운트된다. 편집은 호스트에서, 빌드·실행은 컨테이너에서 한다.

GPU 가 없거나 코드만 보려면 CPU torch 로 빌드해 수 GB 를 아낀다 (compose 의 `gpus: all` 도 지울 것):

```bash
docker compose build --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cpu
```

GPU 인식 확인 — `install.sh` 의 검증 스텝과 같다:

```bash
python3 -c "import torch; print('torch:', torch.__version__); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU only')"
```

## 빌드·실행 (컨테이너 안)

```bash
source /opt/ros/humble/setup.bash
sudo rosdep init 2>/dev/null || true
rosdep update
rosdep install -i --from-path src --rosdistro humble -y

colcon build --symlink-install
source install/local_setup.bash
```

이미지 안에 `MOVE`/`STOP`(`/go` 서비스 호출) 이 alias 로 들어 있다.

## 실차 시리얼 (아두이노 / RPLidar)

`docker-compose.yml` 의 `# - /dev:/dev` 또는 `devices:` 블록 주석을 해제하고 컨테이너를 재생성한다.
WSL 에서는 Windows 쪽 USB 패스스루(`usbipd`)가 추가로 필요하다.

`src/control/` 의 Arduino 스케치는 컨테이너가 아니라 **호스트/보드 툴체인**에서 다룬다.

## 종료

```bash
docker compose down
xhost -local:docker
```
