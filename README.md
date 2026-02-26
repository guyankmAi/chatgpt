# 城市排水管负载模拟器（暴雨洪涝场景）

这是一个面向新手和工程演示的暴雨洪涝模拟系统：
- CLI 批量模拟
- Web 可视化模拟（表格输入 + JSON）
- 动画回放（逐时步）
- 一键下载 Markdown 报告

> 说明：本项目是“轻量工程近似模型”，在交互体验上参考了 SWMM / InfoWorks ICM / MIKE URBAN 等专业系统常见流程（参数化、分区输入、过程线分析、风险输出），便于教学、预研和方案比较。

## 一、Web 图形界面（推荐）

### Linux / macOS

```bash
./start_web.sh
```

### Windows CMD

```bat
start_web.bat
```

浏览器访问：`http://127.0.0.1:8000`

### Web 功能清单

- **表格参数输入**：管道、汇水区、降雨过程线
- **JSON 上传/粘贴**：与表格双向同步
- **模型高级参数**：
  - `initial_loss_mm`（初损）
  - `runoff_safety_factor`（来流安全系数）
  - `capacity_factor`（能力折减系数）
- **动画模拟**：按时间步动态展示负载条和超载状态
- **报告下载**：点击“下载报告(.md)”导出分析报告

## 二、CLI 快速启动

### Linux / macOS

```bash
./start.sh
```

### Windows CMD

```bat
start.bat
```

## 三、CLI 详细用法

```bash
python3 drainage_simulator.py --config sample_scenario.json --report-file simulation_report.md
```

动画模式：

```bash
python3 drainage_simulator.py --config sample_scenario.json --animate --frame-delay 0.2
```

## 四、参数说明（新手友好）

### 基础输入

- `step_minutes`：时间步长（分钟，>0）
- `pipes[].capacity_m3_s`：管道输水能力（m³/s，>0）
- `catchments[].area_km2`：汇水面积（km²，>0）
- `catchments[].runoff_coefficient`：径流系数（0~1）
- `rainfall_series_mm_h`：降雨过程线（mm/h）

### 模型参数（可选）

- `model_params.initial_loss_mm`：初损（mm）
  - 代表截留、下渗、洼蓄等初期损失
  - 初损越大，前期有效降雨越小
- `model_params.runoff_safety_factor`：来流安全系数（>0）
  - 用于放大不确定性（如短历时极端暴雨）
- `model_params.capacity_factor`：能力系数（>0）
  - 用于折减管网能力，模拟淤积、堵塞、维护不足

## 五、模型方法

核心公式：`Q = 0.278 * C * i * A`

并在此基础上加入三个工程化修正：
1. 初损扣减，计算有效降雨；
2. 来流安全系数放大入流；
3. 能力系数折减管道能力。

## 六、示例配置

见 `sample_scenario.json`（含 `model_params` 示例）。
