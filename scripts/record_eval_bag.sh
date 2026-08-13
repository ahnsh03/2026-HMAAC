#!/usr/bin/env bash
# main 세션 bag. 카메라·라이다·제어를 항상 기록한다.
#
#   source /opt/ros/humble/setup.bash && source install/setup.bash
#   ./scripts/record_eval_bag.sh ~/hmaac_logs/TS/bag
#
#   SKIP_VISUALIZED=1  — 오버레이 영상만 빼고 용량 줄이기
set -euo pipefail

DEST="${1:-}"
if [[ -z "$DEST" ]]; then
  echo "usage: $0 <bag_dir>" >&2
  exit 2
fi

mkdir -p "$DEST"

TOPICS=(
  /image_raw
  /lidar_raw
  /lidar_processed
  /lidar_obstacle_info
  /lidar_lane1_min
  /detections
  /yolov8_lane_info
  /yolov8_traffic_light_info
  /lane_control_info
  /roi_image
  /path_planning_result
  /topic_control_signal
  /finish_stop_reason
)

if [[ "${SKIP_VISUALIZED:-0}" != "1" ]]; then
  TOPICS+=(
    /yolov8_visualized_img
    /path_visualized_img
  )
fi

TOPIC_LIST="$(ros2 topic list 2>/dev/null || true)"
if [[ -z "$TOPIC_LIST" ]]; then
  echo "ros2 topic list 실패. ROS_DOMAIN / source 확인." >&2
  exit 1
fi

if ! grep -qx '/image_raw' <<<"$TOPIC_LIST"; then
  echo "ERROR: /image_raw 가 없다. main.launch 가 떠 있는지 확인." >&2
  exit 1
fi

if ! grep -qx '/lidar_raw' <<<"$TOPIC_LIST"; then
  echo "WARN: /lidar_raw 가 아직 없다. /dev/ttyUSB0 권한을 확인. 토픽이 뜨면 이어서 기록한다." >&2
fi

printf '%s\n' "${TOPICS[@]}" > "$DEST/topics.txt"
echo "recording ${#TOPICS[@]} topics -> $DEST/eval"
printf '  %s\n' "${TOPICS[@]}"
exec ros2 bag record -o "$DEST/eval" "${TOPICS[@]}"
