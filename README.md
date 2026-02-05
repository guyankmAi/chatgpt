# 桌面提醒程序（Python + Tkinter）

这是一个简单的桌面提醒小工具：

- 可设置提醒间隔（分钟，支持小数）
- 可设置提醒内容（如“起来拉伸 3 分钟”）
- 到时间后弹窗提醒，点击后自动继续下一轮

## 1) 直接运行 Python 版本

确保你安装了 Python 3（Tkinter 通常随 Python 自带）：

```bash
python3 desktop_reminder.py
```

## 2) 打包成 Windows `.exe`

> 注意：Windows 的 `.exe` 建议在 **Windows 系统** 上打包。
> Linux/macOS 环境通常不能直接产出可在 Windows 运行的 exe。

### 方式 A：一键脚本（推荐）

在 Windows 的命令提示符中执行：

```bat
build_exe.bat
```

打包完成后，生成文件在：

```text
dist\桌面提醒助手.exe
```

### 方式 B：手动命令

```bat
python -m pip install -U pip pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name 桌面提醒助手 desktop_reminder.py
```

### 方式 C：使用 spec 文件（便于后续定制）

```bat
python -m pip install -U pyinstaller
pyinstaller desktop_reminder.spec
```

## 3) 使用说明

1. 输入提醒间隔（例如 `30` 表示每 30 分钟提醒一次）
2. 输入提醒内容
3. 点击“开始提醒”
4. 若要结束，点击“停止提醒”

## 4) 场景示例

- 久坐办公：每 45 分钟提醒站起来活动
- 学习专注：每 25 分钟提醒休息眼睛
- 饮水提醒：每 60 分钟提醒喝水
