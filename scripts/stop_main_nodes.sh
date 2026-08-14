#!/usr/bin/env bash
# main.launch 잔여 노드와 OpenCV 창을 닫는다.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INSTALL="${WS_ROOT}/install"

WINDOW_NAMES=(
  race_viz
  lane2_control_bev
  path_visualized_img
  yolov8_visualized_img
  'Camera Image'
  'Saved Image'
  'Video Frame'
  bev_calibrator
)

if command -v wmctrl >/dev/null 2>&1; then
  for name in "${WINDOW_NAMES[@]}"; do
    wmctrl -c "$name" >/dev/null 2>&1 || true
  done
fi

NODES=(
  image_publisher_node
  yolov8_node
  lane_info_extractor_node
  traffic_light_detector_node
  lidar_publisher_node
  lidar_processor_node
  lidar_obstacle_detector_node
  motion_planner_node
  path_planner_node
  serial_sender_node
  yolov8_visualizer_node
  viz_mosaic_node
  path_visualizer_node
  bev_calibrator_node
)

for name in "${NODES[@]}"; do
  pkill -TERM -f "${INSTALL}/.*/${name}" >/dev/null 2>&1 || true
done

sleep 0.4

for name in "${NODES[@]}"; do
  pkill -KILL -f "${INSTALL}/.*/${name}" >/dev/null 2>&1 || true
done

if command -v wmctrl >/dev/null 2>&1; then
  for name in "${WINDOW_NAMES[@]}"; do
    wmctrl -c "$name" >/dev/null 2>&1 || true
  done
fi
