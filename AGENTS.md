# Codex 规则

## 中文 Markdown 编码

- 中文 `.md` 文件必须使用 UTF-8 读取和写入。
- 禁止用 `type`、`cat` 或默认 `Get-Content` 读取中文文档。
- 推荐使用 `Get-Content -Raw -Encoding UTF8` 或 Python `read_text(encoding="utf-8")`。
- 如果出现乱码、`�` 或问号，必须停止修改，重新按 UTF-8 读取，不能根据乱码改写文档。
