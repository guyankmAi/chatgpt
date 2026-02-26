#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/2] 运行城市排水暴雨模拟..."
python3 drainage_simulator.py --config sample_scenario.json --report-file simulation_report.md

echo "[2/2] 完成。报告文件: $SCRIPT_DIR/simulation_report.md"
