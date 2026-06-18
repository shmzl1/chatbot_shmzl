# Codex 协作指南

本项目当前原则是只保留最新机制，错误必须暴露。

## 中文 Markdown 编码规则

中文 Markdown 文档必须按 UTF-8 读取和写入，包括根目录文档、`docs/` 下的说明文档和中文命名的 `.md` 文件。

在 PowerShell 中读取中文 Markdown 时，禁止使用 `type`、`cat` 或不带编码参数的默认 `Get-Content`。推荐使用：

```powershell
Get-Content -Raw -Encoding UTF8 docs/CODEX_GUIDE.md
```

如果读取结果中出现乱码、`�` 或异常问号，必须立即停止修改当前文档，重新按 UTF-8 读取原文件。

## 默认数据库

默认数据库是 SQLite：

```text
backend/data/chatbot.db
```

普通运行不需要 Docker、PostgreSQL 或 Adminer。不要恢复旧数据库 URL 配置，不要让普通启动脚本调用 Docker。

SQLite 迁移位于：

```text
backend/database/sqlite_migrations/
```

## 文件位置

- 唯一 env 示例：`backend/.env.example`。
- 用户本地真实配置：`backend/.env`。
- 默认 SQLite 文件：`backend/data/chatbot.db`。
- 默认上传目录：`backend/data/uploads/`。
- 后端依赖文件：`backend/requirements.txt`。
- 唯一前端：`frontend/desktop/`。
- 启动/暂停脚本：`scripts/runtime/`。

不要恢复 `frontend/simple_web`，不要恢复旧 HTML + app.js 前端，不要恢复 `/app/` 静态主界面。

## 不要自动执行

除非用户明确要求，不要自动执行：

- `uvicorn main:app --reload`
- `git commit`
- `git push`

文档里可以告诉用户手动执行正确命令，但 Codex 不要代替用户启动服务、删除容器或提交代码。

## 后端依赖

普通启动依赖不包含数据库驱动扩展包，SQLite 使用 Python 标准库。

## LLM

普通聊天只走 `CHAT_*`。人设编辑只走 `PERSONA_EDITOR_*`。两个 provider 都只能是 `openai`。

缺配置、模型失败、超时、JSON 解析失败都应直接报错，并说明 profile、model 和具体错误；错误信息不能包含 API Key。

不要恢复旧 `OPENAI_*`、`LLM_PROVIDER`、`auto`、`mock` 或 `fallback`。

## 本地用户

项目是 Windows 本地单用户模式，不需要注册、登录、密码、JWT 或 Bearer Token 登录锁。后端会自动确保 `users` 表里有一个默认本地用户；`get_current_user` 只是兼容依赖名，必须直接返回默认用户。

如果 SQLite 中已有且只有一个用户，复用该用户；如果有多个用户，必须抛出明确错误，不要随机选。

## 日记

日记模块位于 `backend/modules/diary/`。日记正文和附件元数据保存在 SQLite，图片文件保存在 `backend/data/uploads/diary/images/`。

聊天请求只有显式传入 `diary_entry_id` 时，才能通过 `modules.diary.context` 读取该篇日记。普通聊天不应读取全部日记。从日记页点击“让角色读这篇日记”时，前端应开启新对话，避免把日记上下文混入无关历史会话。

## 聊天会话

正式会话接口位于 `/chat/sessions`，前端不要依赖 `/debug/sessions`。`/debug/sessions` 只保留给调试入口。

新对话在用户发送第一条消息时才创建，不插入空会话。标题由第一条用户消息清理后截断生成，不调用 LLM。会话列表按当前本地用户过滤，支持搜索标题、用户消息和角色回复。

归档会话只设置 `chat_sessions.is_archived=1` 和 `archived_at`，不删除 `chat_turns`。归档会话允许读取但不能继续发送，恢复后才能继续聊天。

聊天、日记和日程共享当前角色选择。前端只保存当前角色 ID 到 localStorage，不能写硬编码角色列表，不能在聊天发送逻辑里静默回退到 `role01` 或列表第一项。打开历史会话时必须按该会话 `character_id` 同步当前角色；在已有会话中切换角色时必须开启新对话。

`role01` 是正式系统默认角色，不是 mock。首次启动或没有保存角色时只能在确认角色列表存在 `role01` 后选择它；保存角色有效时继续使用保存角色；保存角色失效时恢复 `role01`；`role01` 缺失时必须明确报错并禁止角色相关操作。不要用 `characters[0]`、`characters?.[0]` 或角色列表第一项替代默认角色规则。

日记页“让角色读这篇日记”使用当前选中角色并开启新对话。日程数据不按角色隔离，也不应因为当前角色变化而过滤、复制或改写任务。

## 日程

日程模块位于 `backend/modules/schedule/`。第一阶段 MVP 使用 `schedule_items`、`schedule_occurrences`、`schedule_completion_logs` 三张 SQLite 表，不创建 `schedule_plans`。

日程接口由 `backend/main.py` 注册到 `/schedule`。前端 `frontend/desktop/src/pages/SchedulePage.tsx` 通过 `scheduleApi.ts` 调用真实 FastAPI 接口，不使用 mock、fallback 或 localStorage 保存任务。

第一阶段只支持任务 CRUD、选中日期任务、月历汇总、完成、跳过和延期。延期必须保留旧 occurrence 并创建新 occurrence。计划、自动复习、AI 排程、系统通知和聊天集成属于后续阶段。普通聊天不应自动读取日程。

日程筛选默认收起在“筛选”入口中。不要重新加入常驻左侧筛选栏，也不要把全部类型、全部状态和完整状态统计重复铺在主界面上。

## 桌面端服务状态

后端连接正常时，桌面端不显示“服务正常”类常驻状态。只有连接失败时显示简短错误提示，并提供重试和进入设置的按钮。提示不展示 URL、IP 或端口，也不要使用浏览器 alert。

正式后端默认不注册 `/debug/*` 路由。不要让桌面端重新依赖 debug API；需要正式能力时应接入 `modules/*/api.py` 中的正式接口。

## relationship_memory

关系记忆使用 `relationship_memory_events` 表。普通聊天读取有效关系记忆加入长期上下文，同时继续保留 `long_term_memories` 兼容。

记忆必须分层读取：`is_pinned=true` 或 `read_policy=always` 的 pinned 记忆每次 prompt 必读，不参与 topK；普通记忆只有 `status=active`、`read_policy=relevant` 且未过期时才按 topK 进入 prompt；`archived`、`superseded`、`deleted`、`read_policy=never` 或已过期的记忆不能进入 prompt。

## 人设编辑

`finalize` 使用 patch 模式：模型只输出 patch JSON，后端合并 patch，生成 `preview_character_json`，校验通过后返回。`apply` 必须由用户确认后才写入。

固定核心人设不可被 AI 自动修改、删除、覆盖或压缩；可变补充人设可以在用户确认 apply 后压缩并归档。

桌面端聊天页的人设修正入口必须使用当前会话自己的 `character_id` 和正式 turns 数据。不能用全局角色选择器误改其他角色，不能固定 `role01`，不能用角色列表第一项作为静默兜底。

人设修正前端流程必须先保存逐轮反馈到 `/feedback/persona/turn`，再调用 persona-review chat 与人设编辑 AI 讨论。人设编辑 AI 不是聊天角色本人；讨论记录不能写入普通聊天会话、长期记忆或关系记忆。

`finalize` 只生成预览和字段差异，不写角色文件。`apply` 必须经过用户确认，确认文案要说明只影响后续回复、历史聊天不会改变。`rollback` 只恢复最近一次备份，不能声称可恢复任意历史版本。受保护字段如 `id`、`display_name`、`avatar_url`、`voice`、`gptsovits_base_url`、`ref_audio_path`、`prompt_text` 不提供编辑入口，前端发现预览中这些字段变化时应阻止应用，后端校验仍是最终防线。
