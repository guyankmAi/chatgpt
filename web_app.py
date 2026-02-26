#!/usr/bin/env python3
"""城市暴雨洪涝模拟 Web 界面。"""

from __future__ import annotations

from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List
import argparse
import json

from drainage_simulator import Catchment, DrainageSimulator, Pipe, SimulationResult


def build_report_markdown(simulator: DrainageSimulator, results: List[SimulationResult]) -> str:
    pipe_names = list(simulator.pipes.keys())
    peak_overflow = {
        name: max(item.overflow_by_pipe[name] for item in results) for name in pipe_names
    }
    peak_util = {
        name: max(item.utilization_by_pipe[name] for item in results) for name in pipe_names
    }

    lines = [
        "# 城市排水暴雨模拟报告",
        "",
        f"- 生成时间: {datetime.now().isoformat(timespec='seconds')}",
        f"- 时间步数量: {len(results)}",
        "",
        "## 管道风险总览",
        "",
        "| 管道 | 设计能力(m3/s) | 峰值负载率(%) | 峰值溢流(m3/s) | 风险等级 |",
        "|---|---:|---:|---:|---|",
    ]

    for name in pipe_names:
        risk = "高" if peak_util[name] > 150 else ("中" if peak_util[name] > 100 else "低")
        lines.append(
            f"| {name} | {simulator.pipes[name].capacity_m3_s:.2f} | {peak_util[name]:.1f} | {peak_overflow[name]:.2f} | {risk} |"
        )

    return "\n".join(lines)


def run_simulation(config: Dict[str, Any]) -> Dict[str, Any]:
    pipes = [Pipe(**pipe) for pipe in config["pipes"]]
    catchments = [Catchment(**item) for item in config["catchments"]]
    rainfall = config["rainfall_series_mm_h"]
    step = int(config.get("step_minutes", 10))

    simulator = DrainageSimulator(pipes, catchments)
    results = simulator.simulate(rainfall, step_minutes=step)

    pipe_names = list(simulator.pipes.keys())
    risk_summary = []
    for name in pipe_names:
        peak_overflow = max(r.overflow_by_pipe[name] for r in results)
        peak_util = max(r.utilization_by_pipe[name] for r in results)
        risk_level = "高" if peak_util > 150 else ("中" if peak_util > 100 else "低")
        risk_summary.append(
            {
                "pipe": name,
                "capacity_m3_s": simulator.pipes[name].capacity_m3_s,
                "peak_utilization_pct": peak_util,
                "peak_overflow_m3_s": peak_overflow,
                "risk_level": risk_level,
            }
        )

    serial_results = [
        {
            "time_min": r.time_min,
            "rainfall_mm_h": r.rainfall_mm_h,
            "inflow_by_pipe": r.inflow_by_pipe,
            "overflow_by_pipe": r.overflow_by_pipe,
            "utilization_by_pipe": r.utilization_by_pipe,
        }
        for r in results
    ]

    return {
        "pipe_names": pipe_names,
        "results": serial_results,
        "risk_summary": risk_summary,
        "report_markdown": build_report_markdown(simulator, results),
    }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Dict[str, Any], code: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            html = Path("web/index.html").read_text(encoding="utf-8").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/simulate":
            self._send_json({"error": "Not Found"}, code=404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
            result = run_simulation(payload)
            self._send_json(result)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"error": str(exc)}, code=400)


def main() -> None:
    parser = argparse.ArgumentParser(description="城市暴雨洪涝模拟系统 Web 服务")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Web 模拟系统启动: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
