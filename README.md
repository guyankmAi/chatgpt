# 报告/文档审查助手（HTML）

一个轻量的本地网页程序：
- 上传报告文件（Word/PDF/TXT 等）与审查标准；
- 调用 DeepSeek (`deepseek-chat` 或 `deepseek-reasoner`) 生成逐条审查意见；
- 一键导出 Word 审查报告（`.doc`）。

## 使用

```bash
node server.js
```

浏览器访问：`http://localhost:8080`

## DeepSeek 参数

- Base URL: `https://api.deepseek.com/v1`
- 模型：
  - `deepseek-chat`（DeepSeek-V3）
  - `deepseek-reasoner`（DeepSeek-R1）

## 注意

- 浏览器端对 `.pdf/.doc/.docx` 无法像后端库那样完整提取全文，当前实现会附带文件头特征并建议用户粘贴关键条文以提升准确率。
- 导出的 Word 为 HTML 兼容 `.doc`，可直接用 Word 打开与再编辑。
