#!/usr/bin/env bash
# 실차 평가 bag. 없는 토픽은 ros2 bag record 가 경고만 하고 넘어가도록
# 존재하는 것만 고른다.
#
#   ./scripts/record_eval_bag.sh ~/hmaac_logs/TS/bag
set -euo pipefail

DEST="${1:-}"
if [[ -z "$DEST" ]]; then
  echo "usage: $0 <bag_dir>" >&2
  exit 2
fi

mkdir -p "$DEST"

CANDIDATES=(
  /image_raw
  /detections
  /yolov8_lane_info
  /yolov8_traffic_light_info
  /roi_image
  /path_planning_result
  /topic_control_signal
  /control_debug
  /debug_markers
  /yolov8_visualized_img
  /path_visualized_img
  /control_hud_img
  /lidar_raw
  /lidar_processed
  /lidar_obstacle_info
  /lidar_visualized_img
)

TOPICS=()
for t in "${CANDIDATES[@]}"; do
  if ros2 topic list 2>/dev/null | grep -qx "$t"; then
    TOPICS+=("$t")
  fi
done

if [[ ${#TOPICS[@]} -eq 0 ]]; then
  echo "기록할 토픽이 없음. ROS_DOMAIN / source 확인." >&2
  ros2 topic list || true
  exit 1
fi

echo "recording ${#TOPICS[@]} topics -> $DEST"
printf '  %s\n' "${TOPICS[@]}"
exec ros2 bag record -o "$DEST/eval" "${TOPICS[@]}"
