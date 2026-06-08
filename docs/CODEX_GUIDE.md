# Codex 协作指南

本文档说明 Codex 在本项目中改代码和读文档时应遵守的边界。

## 基本原则

- 先读现有代码，再决定改法。
- 优先复用已有模块和服务。
- 不做用户没有要求的大重构。
- 不恢复 mock 或静默兜底。
- 不随意修改数据库结构。
- 不提交 Git。
- 不启动长期运行的服务，除非用户明确要求。

## 人物系统边界

人物相关功能集中在：

```text
backend/modules/characters/
```

新增人物读写能力时，优先使用以下文件：

- `repository.py`
- `pack_loader.py`
- `pack_writer.py`
- `validator.py`
- `service.py`
- `api.py`

不要在聊天、语音、检索或人设编辑模块中重新拼接人物包路径。

## 人设编辑边界

人设编辑流程必须保持安全：

- `chat` 只讨论修改方向。
- `finalize` 只生成最终方案和预览 JSON。
- `apply` 在用户确认后才写入 `character.json`。
- `rollback` 只恢复上一版备份。

写入角色包必须经过人物模块的写入和校验逻辑。

## 文档要求

Markdown 文档统一使用 UTF-8。

写文档时保持以下格式：

- 标题单独成行。
- 段落之间留空行。
- 列表项逐行书写。
- 命令使用 fenced code block。
- 不把大段文字压成一行。

如果 AI 工具读取文档失败，优先检查编码、换行和过长单行。

## 轻量检查

常用检查命令：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m compileall .
```

如果只是改文档，可以额外检查 Markdown 是否能按 UTF-8 读取。

## 禁止事项

- 不运行 `docker compose down -v`。
- 不删除数据库、聊天记录、记忆和知识库。
- 不永久删除角色包。
- 不绕过 `.trash` 删除人物。
- 不把官方素材、语音和模型权重提交到 Git。
