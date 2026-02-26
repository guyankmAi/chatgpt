#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "启动专业暴雨洪涝模拟系统 Web 界面: http://127.0.0.1:8000"
python3 web_app.py --host 0.0.0.0 --port 8000
