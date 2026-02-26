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
    name: str
    capacity_m3_s: float


@dataclass
class Catchment:
    name: str
    area_km2: float
    runoff_coefficient: float
    pipe_name: str


@dataclass
class ModelParams:
    """模型高级参数（可选）。"""

    initial_loss_mm: float = 0.0
    runoff_safety_factor: float = 1.0
    capacity_factor: float = 1.0


@dataclass
class SimulationResult:
    time_min: int
    rainfall_mm_h: float
    effective_rainfall_mm_h: float
    inflow_by_pipe: Dict[str, float]
    overflow_by_pipe: Dict[str, float]
    utilization_by_pipe: Dict[str, float]


class DrainageSimulator:
    """基于理性公式的城市排水负载模拟器。"""

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

        for c in self.catchments:
            if c.pipe_name not in self.pipes:
                raise ValueError(f"汇水区 {c.name} 引用的管道 {c.pipe_name} 不存在")
            if c.area_km2 <= 0:
                raise ValueError(f"汇水区 {c.name} 面积必须大于 0")
            if not (0 <= c.runoff_coefficient <= 1):
                raise ValueError(f"汇水区 {c.name} 的径流系数必须介于 0~1")

    @staticmethod
    def runoff_flow_m3_s(rainfall_mm_h: float, area_km2: float, runoff_coeff: float) -> float:
        return 0.278 * runoff_coeff * rainfall_mm_h * area_km2

    @staticmethod
    def _effective_rainfall_series(
        rainfall_series_mm_h: List[float], step_minutes: int, initial_loss_mm: float
    ) -> List[float]:
        """按初损扣减得到有效降雨序列。"""
        remain = max(0.0, initial_loss_mm)
        step_hour = step_minutes / 60.0
        out: List[float] = []
        for rain in rainfall_series_mm_h:
            depth = max(0.0, rain) * step_hour
            deducted = min(remain, depth)
            remain -= deducted
            eff_depth = max(0.0, depth - deducted)
            out.append(eff_depth / step_hour if step_hour > 0 else 0.0)
        return out

    def simulate(
        self,
        rainfall_series_mm_h: List[float],
        step_minutes: int = 10,
        model_params: ModelParams | None = None,
    ) -> List[SimulationResult]:
        if step_minutes <= 0:
            raise ValueError("时间步长必须大于 0")

        params = model_params or ModelParams()
        if params.runoff_safety_factor <= 0:
            raise ValueError("runoff_safety_factor 必须大于 0")
        if params.capacity_factor <= 0:
            raise ValueError("capacity_factor 必须大于 0")

        effective_rain = self._effective_rainfall_series(
            rainfall_series_mm_h, step_minutes, params.initial_loss_mm
        )

        results: List[SimulationResult] = []
        for idx, rainfall_eff in enumerate(effective_rain):
            inflow = {name: 0.0 for name in self.pipes}
            overflow = {name: 0.0 for name in self.pipes}
            utilization = {name: 0.0 for name in self.pipes}

            for c in self.catchments:
                q = self.runoff_flow_m3_s(
                    rainfall_mm_h=rainfall_eff,
                    area_km2=c.area_km2,
                    runoff_coeff=c.runoff_coefficient,
                )
                inflow[c.pipe_name] += q * params.runoff_safety_factor

            for pipe_name, q_in in inflow.items():
                cap = self.pipes[pipe_name].capacity_m3_s * params.capacity_factor
                overflow[pipe_name] = max(0.0, q_in - cap)
                utilization[pipe_name] = q_in / cap * 100

            results.append(
                SimulationResult(
                    time_min=idx * step_minutes,
                    rainfall_mm_h=rainfall_series_mm_h[idx],
                    effective_rainfall_mm_h=rainfall_eff,
                    inflow_by_pipe=inflow,
                    overflow_by_pipe=overflow,
                    utilization_by_pipe=utilization,
                )
            )

        return results


def load_config(path: str) -> tuple[List[Pipe], List[Catchment], List[float], int, ModelParams]:
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    pipes = [Pipe(**p) for p in config["pipes"]]
    catchments = [Catchment(**c) for c in config["catchments"]]
    rainfall = config["rainfall_series_mm_h"]
    step = config.get("step_minutes", 10)
    params = ModelParams(**config.get("model_params", {}))
    return pipes, catchments, rainfall, step, params


def utilization_bar(utilization_pct: float, width: int = 24) -> str:
    ratio = min(utilization_pct / 100.0, 1.0)
    filled = int(width * ratio)
    over = "!" if utilization_pct > 100 else ""
    return f"[{'#' * filled}{'.' * (width - filled)}]{over}"


def print_animation(results: List[SimulationResult], pipe_names: List[str], frame_delay: float = 0.4) -> None:
    print("\n=== 暴雨排水动画模拟（终端帧动画）===")
    for r in results:
        print("\033[2J\033[H", end="")
        print(
            f"时间: {r.time_min:>3} min | 原始降雨: {r.rainfall_mm_h:>5.1f} mm/h | 有效降雨: {r.effective_rainfall_mm_h:>5.1f} mm/h"
        )
        print("-" * 100)
        for name in pipe_names:
            inflow = r.inflow_by_pipe[name]
            overflow = r.overflow_by_pipe[name]
            util = r.utilization_by_pipe[name]
            status = "超负荷" if util > 100 else "正常"
            print(
                f"{name:<12} | 入流 {inflow:>6.2f} m3/s | 溢流 {overflow:>6.2f} m3/s | 负载 {util:>6.1f}% {utilization_bar(util)} {status}"
            )
        time.sleep(frame_delay)
    print("\n动画播放结束。")


def summarize(results: List[SimulationResult], pipe_names: List[str]) -> str:
    lines = []
    header = (
        "time(min) | rain(mm/h) | eff_rain(mm/h) | "
        + " | ".join([f"{n}:inflow/overflow/util(%)" for n in pipe_names])
    )
    lines.append(header)
    lines.append("-" * len(header))
    for r in results:
        row = [f"{r.time_min:>8}", f"{r.rainfall_mm_h:>10.1f}", f"{r.effective_rainfall_mm_h:>13.1f}"]
        for name in pipe_names:
            row.append(
                f"{r.inflow_by_pipe[name]:>5.2f}/{r.overflow_by_pipe[name]:>5.2f}/{r.utilization_by_pipe[name]:>6.1f}"
            )
        lines.append(" | ".join(row))
    return "\n".join(lines)


def generate_report(
    report_path: str,
    config_path: str,
    simulator: DrainageSimulator,
    results: List[SimulationResult],
    model_params: ModelParams,
) -> None:
    pipe_names = list(simulator.pipes.keys())
    peak_overflow = {n: max(x.overflow_by_pipe[n] for x in results) for n in pipe_names}
    peak_util = {n: max(x.utilization_by_pipe[n] for x in results) for n in pipe_names}

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 城市排水暴雨模拟报告\n\n")
        f.write(f"- 生成时间: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"- 配置文件: {config_path}\n")
        f.write(f"- 时间步数量: {len(results)}\n")
        f.write(
            f"- 模型参数: initial_loss_mm={model_params.initial_loss_mm}, runoff_safety_factor={model_params.runoff_safety_factor}, capacity_factor={model_params.capacity_factor}\n\n"
        )

        f.write("## 管道风险总览\n\n")
        f.write("| 管道 | 设计能力(m3/s) | 峰值负载率(%) | 峰值溢流(m3/s) | 风险等级 |\n")
        f.write("|---|---:|---:|---:|---|\n")
        for name in pipe_names:
            risk = "高" if peak_util[name] > 150 else ("中" if peak_util[name] > 100 else "低")
            f.write(
                f"| {name} | {simulator.pipes[name].capacity_m3_s:.2f} | {peak_util[name]:.1f} | {peak_overflow[name]:.2f} | {risk} |\n"
            )

        f.write("\n## 时序明细\n\n")
        f.write(summarize(results, pipe_names))
        f.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="城市排水管网暴雨洪涝负载模拟")
    parser.add_argument("--config", default="sample_scenario.json")
    parser.add_argument("--animate", action="store_true")
    parser.add_argument("--frame-delay", type=float, default=0.4)
    parser.add_argument("--report-file", default="simulation_report.md")
    args = parser.parse_args()

    pipes, catchments, rainfall, step, params = load_config(args.config)
    simulator = DrainageSimulator(pipes, catchments)
    results = simulator.simulate(rainfall, step_minutes=step, model_params=params)
    pipe_names = list(simulator.pipes.keys())

    print(summarize(results, pipe_names))
    generate_report(args.report_file, args.config, simulator, results, model_params=params)
    print(f"\n模拟报告已生成: {args.report_file}")

    if args.animate:
        print_animation(results, pipe_names, frame_delay=max(0.0, args.frame_delay))


if __name__ == "__main__":
    main()
