# ROS2 환경 · 빌드

출처: PDF p.148–151

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash

# 영구화 (아직 안 했다면)
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
# 터미널 재실행

colcon build --symlink-install
# 6 packages finished 확인
# 실패 시:
#   rm -rf build install log
#   colcon build --symlink-install

source ./install/setup.bash
```

빌드 후 `build/`, `install/`, `log/` 생성을 `ls`로 확인한다.
