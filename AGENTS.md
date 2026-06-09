# Codex 规则

## 中文 Markdown 编码

- 中文 `.md` 文件必须使用 UTF-8 读取和写入。
- 禁止用 `type`、`cat` 或默认 `Get-Content` 读取中文文档。
- 推荐使用 `Get-Content -Raw -Encoding UTF8` 或 Python `read_text(encoding="utf-8")`。
- 如果出现乱码、`�` 或问号，必须停止修改，重新按 UTF-8 读取，不能根据乱码改写文档。

## 编码规则

- 不允许写兜底机制，尽量减少硬编码
- 在重构项目的前端，后端或数据库时，不要兼容旧版本。该删的代码全部删掉。
