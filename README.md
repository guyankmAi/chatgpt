# 城市排水管负载模拟器（暴雨洪涝场景）

这是一个可运行的“专业版演示系统”：
- 支持命令行模拟（CLI）
- 支持 Web 界面模拟（可上传 JSON 或直接输入数据）
- 自动生成模拟报告
- 支持终端动画（CLI）

## 一、Web 图形界面（推荐）

### Linux / macOS

```bash
./start_web.sh
```

### Windows CMD

```bat
start_web.bat
```

启动后在浏览器访问：

- `http://127.0.0.1:8000`

在页面中你可以：
- 用“表格”维护管道、汇水区、降雨过程参数
- 上传配置文件（JSON）或直接粘贴 JSON
- 在“参数表 ⇄ JSON”之间双向同步
- 一键运行模拟并查看风险总览、时序结果、报告预览
- 播放动画模拟（逐时间步显示管道负载变化）

## 二、CLI 一键启动（快速测试）

### Linux / macOS

```bash
./start.sh
```

### Windows CMD

```bat
start.bat
```

该命令会自动使用内置测试数据完成模拟并生成 `simulation_report.md` 报告。

## 三、CLI 详细用法

### 标准模拟 + 生成报告

```bash
python3 drainage_simulator.py --config sample_scenario.json --report-file simulation_report.md
```

### 动画模拟（终端帧动画）

```bash
python3 drainage_simulator.py --animate --frame-delay 0.2
```

## 配置格式说明

示例见 `sample_scenario.json`，结构如下：

- `step_minutes`: 时间步长（分钟）
- `pipes`: 管道数组（`name`, `capacity_m3_s`）
- `catchments`: 汇水区数组（`name`, `area_km2`, `runoff_coefficient`, `pipe_name`）
- `rainfall_series_mm_h`: 降雨序列（mm/h）

## 模型说明

采用简化理性公式：`Q = 0.278 * C * i * A`
- `Q`：入流量（m3/s）
- `C`：径流系数
- `i`：降雨强度（mm/h）
- `A`：汇水面积（km2）

系统会输出每根管道在每个时刻的：
- `inflow`：瞬时入流
- `overflow`：溢流量
- `util(%)`：负载率


## 四、Web 输入参数说明（建议）

Web 页面内置了参数说明表，建议重点关注：

- `capacity_m3_s`：管道过流能力，必须大于 0。
- `runoff_coefficient`：径流系数 0~1，硬化区通常更高。
- `rainfall_series_mm_h`：建议覆盖暴雨全过程（起涨-峰值-回落）。
- `step_minutes`：步长越小，时序细节越丰富，但结果数据量更大。
