# 项目协作规则

## 中文 Markdown 编码

- 中文 `.md` 文件必须使用 UTF-8 读取和写入。
- 禁止用 `type`、`cat` 或默认 `Get-Content` 读取中文文档。
- 推荐使用 `Get-Content -Raw -Encoding UTF8` 或 Python `read_text(encoding="utf-8")`。
- 如果出现乱码、`�` 或问号，必须停止修改，重新按 UTF-8 读取，不能根据乱码改写文档。

## 当前架构边界

- 项目是 Windows 本地单用户桌面应用，不恢复注册、登录、JWT 或 Bearer Token 登录锁。
- 默认数据库是 SQLite，默认文件为 `backend/data/chatbot.db`，迁移位于 `backend/database/sqlite_migrations/`。不要恢复 PostgreSQL、Docker、Adminer、旧数据库 URL 或依赖容器的普通启动路径。
- 唯一前端是 `frontend/desktop/`。不要恢复 `frontend/simple_web`、旧 HTML + app.js 前端或 `/app/` 静态主界面。
- 后端入口是 `backend/main.py`，正式路由来自 `backend/modules/*`。正式后端和前端不得恢复或依赖 `/debug/*` 路由。
- 普通聊天的 LLM 配置只使用 `CHAT_*`，人设编辑的 LLM 配置只使用 `PERSONA_EDITOR_*`。不要恢复旧 `OPENAI_*`、`LLM_PROVIDER`、`auto`、`mock` 或 `fallback` 路径；配置和模型错误应明确暴露，但不得泄露 API Key。

## 实现约束

- 不允许用兜底机制隐藏错误，尽量减少硬编码。缺少配置、角色包或必要数据时应明确报错。
- 重构前端、后端或数据库时以当前版本为准，不为旧实现增加兼容层；过期代码和文件只在当前任务明确授权时清理。
- `role01` 是系统定义的首次启动默认角色，不是 mock，也不是废弃兜底。保存角色有效时继续使用；保存角色失效时恢复 `role01`。默认角色逻辑必须先确认正式角色包真实存在；如果 `role01` 缺失，应明确报错，不能改用角色列表第一项。
- 日记和日程不得自动进入聊天 prompt。只有用户明确选择“让角色读这篇日记”时，才能把该篇日记用于新对话上下文。
- 人设修改必须先生成 preview，再由用户明确确认后应用。`finalize` 不得写角色文件，`apply` 才能写入，`rollback` 只恢复最近一次备份。
- 固定核心人设字段 `id`、`display_name`、`core_personality`、`speaking_style`、`relationship_to_user`、`forbidden`、`reply_patterns`、`lore`、`style_contract` 不可被自动修改、删除、覆盖或压缩；`avatar_url` 和 `voice` 是受保护元数据。

## 操作边界

- 除非用户明确要求，不要自动启动后端、前端开发服务或桌面端。
- 除非用户明确要求，不要执行 `git commit` 或 `git push`。
