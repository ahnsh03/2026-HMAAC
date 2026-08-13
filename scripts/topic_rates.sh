#!/usr/bin/env bash
# 실차 파이프라인 단계별 Hz.
#   source install/setup.bash && ./scripts/topic_rates.sh
set -euo pipefail

WINDOW="${WINDOW:-6}"

TOPICS=(
  /image_raw
  /detections
  /yolov8_lane_info
  /roi_image
  /path_planning_result
  /topic_control_signal
  /yolov8_traffic_light_info
  /yolov8_visualized_img
  /path_visualized_img
  /lidar_raw
  /lidar_processed
  /lidar_obstacle_info
)

printf '%-32s %s\n' "topic" "rate"
printf '%-32s %s\n' "-----" "----"
for topic in "${TOPICS[@]}"; do
  printf '%-32s ' "${topic}"
  if ! ros2 topic list 2>/dev/null | grep -qx "$topic"; then
    echo "not advertised"
    continue
  fi
  timeout "${WINDOW}" ros2 topic hz "${topic}" 2>/dev/null \
    | grep -m1 'average rate' \
    || echo "no data"
done
