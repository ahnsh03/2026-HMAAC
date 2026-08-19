#!/usr/bin/env bash
# 시도 폴더를 만들고 bag 을 켠다. Ctrl+C 로 bag 과 함께 종료.
#
# 기본은 main.launch.py 의 record:=true 로 같이 기록한다.
# 이 스크립트는 main 을 record:=false 로 켠 뒤 따로 bag 을 쓸 때만 쓴다.
#
#   source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash
#   # 다른 터미널에서 먼저: ros2 launch launch_pkg main.launch.py record:=false
#   ./scripts/run_session.sh
set -euo pipefail

ROOT="${HMAAC_LOG_ROOT:-$HOME/hmaac_logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
SESSION="${ROOT}/${STAMP}"
mkdir -p "$SESSION/bag"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

GIT_SHA="unknown"
if git -C "$WS_ROOT" rev-parse --short HEAD >/dev/null 2>&1; then
  GIT_SHA="$(git -C "$WS_ROOT" rev-parse --short HEAD)"
fi

cat > "$SESSION/meta.json" <<EOF
{
  "stamp": "${STAMP}",
  "session": "${SESSION}",
  "git_sha": "${GIT_SHA}",
  "model": "${MODEL:-}",
  "drive_speed": "${DRIVE_SPEED:-}",
  "c920_profile": "${C920_PROFILE:-match_train}",
  "cam_num": "${CAM_NUM:-}",
  "hostname": "$(hostname)",
  "notes": "${NOTES:-}"
}
EOF

touch "$SESSION/notes.txt"
echo "session=${SESSION}" | tee "$SESSION/session.env"
echo "export HMAAC_SESSION=${SESSION}" >> "$SESSION/session.env"

echo ""
echo "SESSION: $SESSION"
echo "main.launch 가 뜬 뒤 이 창에서 bag 이 돈다. 카메라·라이다·제어를 같이 기록한다."
echo "재생(serial 끄고): ros2 bag play ${SESSION}/bag/eval"
echo "종료: Ctrl+C"
echo ""

cleanup() {
  echo ""
  echo "stopped. 경로: $SESSION"
  echo "재생(serial 끄고): ros2 bag play ${SESSION}/bag/eval"
}
trap cleanup EXIT

"${SCRIPT_DIR}/record_eval_bag.sh" "$SESSION/bag"
