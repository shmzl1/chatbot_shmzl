# 架构说明

后端入口是 `backend/main.py`，路由注册来自 `backend/modules/*`。唯一前端是 `frontend/desktop/`，后端不再挂载旧 `/app/` 静态主界面。

## 项目边界

本项目定位为 Windows 本地单用户桌面端应用。主功能是聊天、日记、日程和设置；角色、人设、关系记忆、知识库是底层能力。

普通运行路径不依赖 Docker、PostgreSQL 或 Adminer。

## 数据库架构

默认数据库是 SQLite：

```text
backend/data/chatbot.db
```

默认上传目录：

```text
backend/data/uploads/
```

默认备份目录：

```text
backend/data/backups/
```

配置项：

```env
APP_DATA_DIR="./data"
SQLITE_DB_PATH="./data/chatbot.db"
UPLOAD_DIR="./data/uploads"
BACKUP_DIR="./data/backups"
```

`backend/services/database_service.py` 是默认 SQLite 数据访问层。它使用 Python 标准库 `sqlite3`，连接时开启：

```text
row_factory = sqlite3.Row
PRAGMA foreign_keys = ON
PRAGMA journal_mode = WAL
```

SQLite migrations 位于：

```text
backend/database/sqlite_migrations/
```

## 数据流

本地用户：

```text
frontend/desktop
  -> GET /auth/me
  -> services.auth_service.ensure_default_user
  -> users singleton row in SQLite
```

聊天：

```text
frontend/desktop
  -> modules.chat.api
  -> /chat/sessions for session list/search/archive
  -> modules.characters.service
  -> relationship_memory / long_term_memories / knowledge retrieval
  -> chat LLM profile
  -> database_service SQLite write
```

聊天会话保存在 `chat_sessions` 和 `chat_turns`。`chat_sessions` 包含 `title`、`is_archived`、`archived_at` 和 `user_id`。新对话第一次发送时才创建真实会话，标题由第一条用户消息裁剪生成；归档只设置软状态，不删除 turn。正式前端只使用 `/chat/sessions`，`/debug/sessions` 仅用于调试。

日记：

```text
frontend/desktop diary page
  -> modules.diary.api
  -> diary_entries / diary_attachments in SQLite
  -> backend/data/uploads/diary/images
```

日程：

```text
frontend/desktop schedule page
  -> modules.schedule.api
  -> modules.schedule.service
  -> modules.schedule.repository
  -> schedule_items / schedule_occurrences / schedule_completion_logs in SQLite
```

日程第一阶段提供任务 CRUD、选中日期任务、月历汇总、完成、跳过和延期。延期不会覆盖历史 occurrence，而是把旧 occurrence 标记为 `postponed`，再创建新的 `pending` occurrence。计划、自动复习、AI 排程、通知和聊天集成属于后续阶段；日程默认不进入聊天 prompt。

人设编辑：

```text
frontend/desktop
  -> characters persona-review endpoints
  -> persona_editor LLM profile
  -> patch
  -> preview_character_json
  -> user confirmed apply
  -> character.json write and optional compaction archive
```

## 本地用户策略

项目不需要注册、登录、密码、JWT 或 Bearer Token。`get_current_user` 保留为依赖函数名，但直接返回默认本地用户。

SQLite 中没有用户时自动创建默认用户；已有一个用户时复用；多个用户时抛出明确错误，避免破坏旧数据关联。

## 人设分层

固定核心人设：`id`、`display_name`、`core_personality`、`speaking_style`、`relationship_to_user`、`forbidden`、`reply_patterns`、`lore`、`style_contract`。AI 不能自动 patch、删除、覆盖或压缩，聊天 prompt 每次完整读取。`avatar_url` 和 `voice` 是受保护元数据。

可变补充人设：`dialogues`、`reactions`、`bad_examples`、`evaluation_criteria`、`revision_notes`。用户确认 apply 后允许按上限压缩并归档。

## 记忆读取

- pinned / always_read：`is_pinned=1` 或 `read_policy=always`，每次 prompt 必读，不参与 topK。
- 普通 active：`status=active`、`read_policy=relevant`、未过期，按重要度和相关性 topK 读取。
- 短期记忆：通过 `expires_at` 控制，过期后不进入 prompt。

`archived`、`superseded`、`deleted`、`read_policy=never`、已过期或 `is_active=0` 的记忆不会进入 prompt。
