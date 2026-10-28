#!/usr/bin/env bash
# 从任意工作目录启动；Python 节点以 20 Hz 持续发送速度。
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/draw_square.py" "$@"
