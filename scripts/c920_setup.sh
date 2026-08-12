#!/usr/bin/env bash
# Logitech C920e V4L2 프로파일.
#   ./scripts/c920_setup.sh list /dev/video0
#   ./scripts/c920_setup.sh match_train /dev/video0   # 권장: 포커스만 잠금, AE/AWB auto
#   ./scripts/c920_setup.sh full_lock /dev/video0     # FT 수집 또는 AE hunting 시
#
# 문서: docs/team/debug-and-incremental-test.md
set -euo pipefail

PROFILE="${1:-list}"
DEV="${2:-/dev/video0}"

if ! command -v v4l2-ctl >/dev/null 2>&1; then
  echo "v4l2-ctl 없음.  sudo apt install v4l-utils" >&2
  exit 1
fi

if [[ ! -e "$DEV" ]]; then
  echo "장치 없음: $DEV" >&2
  echo "v4l2-ctl --list-devices" >&2
  v4l2-ctl --list-devices || true
  exit 1
fi

set_ctrl() {
  local name="$1"
  local value="$2"
  if v4l2-ctl -d "$DEV" --set-ctrl="${name}=${value}" 2>/dev/null; then
    echo "  ${name}=${value}"
  else
    echo "  skip ${name} (이 드라이버에 없음)"
  fi
}

echo "device: $DEV  profile: $PROFILE"
echo "--- current ---"
v4l2-ctl -d "$DEV" --list-ctrls 2>/dev/null | sed 's/^/  /' || true

case "$PROFILE" in
  list)
    echo "--- devices ---"
    v4l2-ctl --list-devices || true
    ;;
  match_train)
    echo "--- apply match_train (focus lock, AE/AWB auto) ---"
    set_ctrl focus_auto 0
    set_ctrl focus_absolute "${FOCUS_ABSOLUTE:-0}"
    # C920: 3 = Aperture Priority Mode
    set_ctrl exposure_auto 3
    set_ctrl auto_exposure 3
    set_ctrl white_balance_temperature_auto 1
    set_ctrl white_balance_automatic 1
    set_ctrl power_line_frequency 2
    set_ctrl backlight_compensation 0
    ;;
  full_lock)
    echo "--- apply full_lock (manual exposure/WB) ---"
    set_ctrl focus_auto 0
    set_ctrl focus_absolute "${FOCUS_ABSOLUTE:-0}"
    set_ctrl exposure_auto 1
    set_ctrl auto_exposure 1
    set_ctrl exposure_absolute "${EXPOSURE_ABSOLUTE:-250}"
    set_ctrl white_balance_temperature_auto 0
    set_ctrl white_balance_automatic 0
    set_ctrl white_balance_temperature "${WB_TEMP:-4000}"
    set_ctrl gain "${GAIN:-0}"
    set_ctrl power_line_frequency 2
    set_ctrl backlight_compensation 0
    ;;
  *)
    echo "usage: $0 {list|match_train|full_lock} [/dev/videoN]" >&2
    echo "env: FOCUS_ABSOLUTE EXPOSURE_ABSOLUTE WB_TEMP GAIN" >&2
    exit 2
    ;;
esac

echo "--- after ---"
v4l2-ctl -d "$DEV" --list-ctrls 2>/dev/null | sed 's/^/  /' || true
echo "USB 재연결 후 다시 실행할 것."
