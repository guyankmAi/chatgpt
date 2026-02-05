import tkinter as tk
from tkinter import messagebox
from datetime import datetime


class DesktopReminderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("桌面提醒小助手")
        self.root.geometry("420x280")
        self.root.resizable(False, False)

        self.interval_var = tk.StringVar(value="30")
        self.task_var = tk.StringVar(value="起来活动一下，做做拉伸，喝口水")
        self.status_var = tk.StringVar(value="状态：未启动")
        self.next_time_var = tk.StringVar(value="下次提醒：--")

        self._after_id: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        frame = tk.Frame(self.root, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text="桌面定时提醒", font=("Microsoft YaHei", 16, "bold"))
        title.pack(anchor="w", pady=(0, 10))

        interval_row = tk.Frame(frame)
        interval_row.pack(fill="x", pady=8)
        tk.Label(interval_row, text="提醒间隔（分钟）：", width=14, anchor="w").pack(side="left")
        tk.Entry(interval_row, textvariable=self.interval_var, width=20).pack(side="left")

        task_row = tk.Frame(frame)
        task_row.pack(fill="x", pady=8)
        tk.Label(task_row, text="提醒内容：", width=14, anchor="w").pack(side="left")
        tk.Entry(task_row, textvariable=self.task_var, width=34).pack(side="left")

        button_row = tk.Frame(frame)
        button_row.pack(fill="x", pady=14)
        tk.Button(button_row, text="开始提醒", width=12, command=self.start).pack(side="left")
        tk.Button(button_row, text="停止提醒", width=12, command=self.stop).pack(side="left", padx=10)

        tk.Label(frame, textvariable=self.status_var, fg="#2f5fa4").pack(anchor="w", pady=4)
        tk.Label(frame, textvariable=self.next_time_var, fg="#4a4a4a").pack(anchor="w", pady=4)

        tips = tk.Label(
            frame,
            text="提示：提醒弹窗出现后点击“确定”，将自动继续下一轮计时。",
            fg="#888888",
            wraplength=380,
            justify="left",
        )
        tips.pack(anchor="w", pady=(14, 0))

    def _parse_interval_ms(self) -> int:
        try:
            minutes = float(self.interval_var.get().strip())
        except ValueError as exc:
            raise ValueError("提醒间隔请输入数字，例如 30 或 0.5") from exc

        if minutes <= 0:
            raise ValueError("提醒间隔必须大于 0")

        return int(minutes * 60 * 1000)

    def _schedule_next(self, interval_ms: int) -> None:
        if self._after_id:
            self.root.after_cancel(self._after_id)

        next_time = datetime.now().timestamp() + interval_ms / 1000
        formatted = datetime.fromtimestamp(next_time).strftime("%H:%M:%S")
        self.next_time_var.set(f"下次提醒：{formatted}")

        self._after_id = self.root.after(interval_ms, self._on_timer)

    def _on_timer(self) -> None:
        self._after_id = None
        task = self.task_var.get().strip() or "该活动啦！"
        messagebox.showinfo("运动提醒", task)

        try:
            interval_ms = self._parse_interval_ms()
        except ValueError as error:
            self.status_var.set(f"状态：输入有误，已停止（{error}）")
            self.next_time_var.set("下次提醒：--")
            return

        self.status_var.set("状态：提醒中")
        self._schedule_next(interval_ms)

    def start(self) -> None:
        try:
            interval_ms = self._parse_interval_ms()
        except ValueError as error:
            messagebox.showerror("输入错误", str(error))
            return

        self.status_var.set("状态：提醒中")
        self._schedule_next(interval_ms)

    def stop(self) -> None:
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

        self.status_var.set("状态：已停止")
        self.next_time_var.set("下次提醒：--")


if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopReminderApp(root)
    root.mainloop()
