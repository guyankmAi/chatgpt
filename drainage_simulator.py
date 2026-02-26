#!/usr/bin/env python3
"""城市排水管网暴雨洪涝负载模拟程序。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
import argparse
import json
import time


@dataclass
class Pipe:
    """单根排水管参数。"""

    name: str
    capacity_m3_s: float


@dataclass
class Catchment:
    """汇水分区参数。"""

    name: str
    area_km2: float
    runoff_coefficient: float
    pipe_name: str


@dataclass
class SimulationResult:
    time_min: int
    rainfall_mm_h: float
    inflow_by_pipe: Dict[str, float]
    overflow_by_pipe: Dict[str, float]
    utilization_by_pipe: Dict[str, float]


class DrainageSimulator:
    """基于简化理性公式的城市排水负载模拟器。"""

    def __init__(self, pipes: List[Pipe], catchments: List[Catchment]):
        self.pipes = {pipe.name: pipe for pipe in pipes}
        self.catchments = catchments
        self._validate_inputs()

    def _validate_inputs(self) -> None:
        if not self.pipes:
            raise ValueError("必须至少提供一根管道")
        if not self.catchments:
            raise ValueError("必须至少提供一个汇水区")

        for pipe in self.pipes.values():
            if pipe.capacity_m3_s <= 0:
                raise ValueError(f"管道 {pipe.name} 的能力必须大于 0")

        for catchment in self.catchments:
            if catchment.pipe_name not in self.pipes:
                raise ValueError(
                    f"汇水区 {catchment.name} 引用的管道 {catchment.pipe_name} 不存在"
                )
            if catchment.area_km2 <= 0:
                raise ValueError(f"汇水区 {catchment.name} 面积必须大于 0")
            if not (0 <= catchment.runoff_coefficient <= 1):
                raise ValueError(
                    f"汇水区 {catchment.name} 的径流系数必须介于 0~1"
                )

    @staticmethod
    def runoff_flow_m3_s(rainfall_mm_h: float, area_km2: float, runoff_coeff: float) -> float:
        """理性公式 Q = 0.278 * C * i * A。"""
        return 0.278 * runoff_coeff * rainfall_mm_h * area_km2

    def simulate(
        self, rainfall_series_mm_h: List[float], step_minutes: int = 10
    ) -> List[SimulationResult]:
        if step_minutes <= 0:
            raise ValueError("时间步长必须大于 0")

        results: List[SimulationResult] = []
        for idx, rainfall in enumerate(rainfall_series_mm_h):
            inflow = {name: 0.0 for name in self.pipes}
            overflow = {name: 0.0 for name in self.pipes}
            utilization = {name: 0.0 for name in self.pipes}

            for catchment in self.catchments:
                q = self.runoff_flow_m3_s(
                    rainfall_mm_h=rainfall,
                    area_km2=catchment.area_km2,
                    runoff_coeff=catchment.runoff_coefficient,
                )
                inflow[catchment.pipe_name] += q

            for pipe_name, q_in in inflow.items():
                cap = self.pipes[pipe_name].capacity_m3_s
                overflow[pipe_name] = max(0.0, q_in - cap)
                utilization[pipe_name] = q_in / cap * 100

            results.append(
                SimulationResult(
                    time_min=idx * step_minutes,
                    rainfall_mm_h=rainfall,
                    inflow_by_pipe=inflow,
                    overflow_by_pipe=overflow,
                    utilization_by_pipe=utilization,
                )
            )

        return results


def load_config(path: str) -> tuple[List[Pipe], List[Catchment], List[float], int]:
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    pipes = [Pipe(**p) for p in config["pipes"]]
    catchments = [Catchment(**c) for c in config["catchments"]]
    rainfall = config["rainfall_series_mm_h"]
    step = config.get("step_minutes", 10)
    return pipes, catchments, rainfall, step


def utilization_bar(utilization_pct: float, width: int = 24) -> str:
    ratio = min(utilization_pct / 100.0, 1.0)
    filled = int(width * ratio)
    over = "!" if utilization_pct > 100 else ""
    return f"[{'#' * filled}{'.' * (width - filled)}]{over}"


def print_animation(
    results: List[SimulationResult], pipe_names: List[str], frame_delay: float = 0.4
) -> None:
    print("\n=== 暴雨排水动画模拟（终端帧动画）===")
    for result in results:
        print("\033[2J\033[H", end="")
        print(
            f"时间: {result.time_min:>3} min | 降雨强度: {result.rainfall_mm_h:>5.1f} mm/h"
        )
        print("-" * 90)
        for pipe_name in pipe_names:
            inflow = result.inflow_by_pipe[pipe_name]
            overflow = result.overflow_by_pipe[pipe_name]
            util = result.utilization_by_pipe[pipe_name]
            bar = utilization_bar(util)
            status = "超负荷" if util > 100 else "正常"
            print(
                f"{pipe_name:<12} | 入流 {inflow:>6.2f} m3/s | 溢流 {overflow:>6.2f} m3/s "
                f"| 负载 {util:>6.1f}% {bar} {status}"
            )
        time.sleep(frame_delay)
    print("\n动画播放结束。")


def summarize(results: List[SimulationResult], pipe_names: List[str]) -> str:
    lines = []
    header = (
        "time(min) | rain(mm/h) | "
        + " | ".join([f"{n}:inflow/overflow/util(%)" for n in pipe_names])
    )
    lines.append(header)
    lines.append("-" * len(header))

    for r in results:
        row = [f"{r.time_min:>8}", f"{r.rainfall_mm_h:>10.1f}"]
        for name in pipe_names:
            row.append(
                f"{r.inflow_by_pipe[name]:>5.2f}/{r.overflow_by_pipe[name]:>5.2f}/{r.utilization_by_pipe[name]:>6.1f}"
            )
        lines.append(" | ".join(row))

    peak_overflow = {
        name: max(item.overflow_by_pipe[name] for item in results) for name in pipe_names
    }
    lines.append("\n峰值溢流量(m3/s):")
    for name in pipe_names:
        lines.append(f"- {name}: {peak_overflow[name]:.2f}")

    return "\n".join(lines)


def generate_report(
    report_path: str,
    config_path: str,
    simulator: DrainageSimulator,
    results: List[SimulationResult],
) -> None:
    pipe_names = list(simulator.pipes.keys())
    peak_overflow = {
        name: max(item.overflow_by_pipe[name] for item in results) for name in pipe_names
    }
    peak_util = {
        name: max(item.utilization_by_pipe[name] for item in results) for name in pipe_names
    }

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 城市排水暴雨模拟报告\n\n")
        f.write(f"- 生成时间: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"- 配置文件: {config_path}\n")
        f.write(f"- 时间步数量: {len(results)}\n\n")

        f.write("## 管道风险总览\n\n")
        f.write("| 管道 | 设计能力(m3/s) | 峰值负载率(%) | 峰值溢流(m3/s) | 风险等级 |\n")
        f.write("|---|---:|---:|---:|---|\n")
        for name in pipe_names:
            capacity = simulator.pipes[name].capacity_m3_s
            risk = "高" if peak_util[name] > 150 else ("中" if peak_util[name] > 100 else "低")
            f.write(
                f"| {name} | {capacity:.2f} | {peak_util[name]:.1f} | {peak_overflow[name]:.2f} | {risk} |\n"
            )

        f.write("\n## 时序明细\n\n")
        f.write(summarize(results, pipe_names))
        f.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="城市排水管网暴雨洪涝负载模拟")
    parser.add_argument(
        "--config",
        default="sample_scenario.json",
        help="配置文件路径(JSON)，默认 sample_scenario.json",
    )
    parser.add_argument(
        "--animate",
        action="store_true",
        help="启用终端动画模拟展示",
    )
    parser.add_argument(
        "--frame-delay",
        type=float,
        default=0.4,
        help="动画每帧间隔秒数，默认 0.4",
    )
    parser.add_argument(
        "--report-file",
        default="simulation_report.md",
        help="模拟报告输出文件路径，默认 simulation_report.md",
    )
    args = parser.parse_args()

    pipes, catchments, rainfall, step = load_config(args.config)
    simulator = DrainageSimulator(pipes, catchments)
    results = simulator.simulate(rainfall, step_minutes=step)
    pipe_names = list(simulator.pipes.keys())

    print(summarize(results, pipe_names))
    generate_report(args.report_file, args.config, simulator, results)
    print(f"\n模拟报告已生成: {args.report_file}")

    if args.animate:
        print_animation(results, pipe_names, frame_delay=max(0.0, args.frame_delay))


if __name__ == "__main__":
    main()
