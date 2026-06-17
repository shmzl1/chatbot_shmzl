# 虚拟人物陪伴系统

本项目是 Windows 本地单用户桌面端虚拟人物陪伴系统。主功能是聊天、日记、日程和设置；角色、人设、记忆、知识库是底层能力。

默认数据库已经迁移为 SQLite。普通用户不再需要 Docker、PostgreSQL 或 Adminer。

## 当前结构

```text
chatbot/
  backend/
    .env.example
    data/
      chatbot.db
      uploads/
      backups/
    database/
      sqlite_migrations/
    main.py
    modules/
    services/
  frontend/
    desktop/
  docs/
  scripts/
    runtime/
```

## 数据库

默认配置：

```env
APP_DATA_DIR="./data"
SQLITE_DB_PATH="./data/chatbot.db"
UPLOAD_DIR="./data/uploads"
BACKUP_DIR="./data/backups"
```

后端启动时会自动创建 `backend/data/`、`backend/data/chatbot.db`、`backend/data/uploads/` 和 `backend/data/backups/`，并执行 `backend/database/sqlite_migrations/` 中尚未执行的迁移。

## 环境变量

复制环境变量示例：

```powershell
cd E:\my_software\chatbot
Copy-Item backend\.env.example backend\.env
```

普通聊天只读取 `CHAT_*`，人设编辑只读取 `PERSONA_EDITOR_*`。不要提交真实 API Key，不要提交 `backend/.env`。

项目不保留旧 `OPENAI_*`、`LLM_PROVIDER`、`auto`、`mock` 或 `fallback` 路径。缺配置、模型失败、JSON 非法都会直接报错。

## 后端启动

安装依赖：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m pip install -r requirements.txt
```

启动后端：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/health
```

## 桌面端启动

```powershell
cd E:\my_software\chatbot\frontend\desktop
npm install
npm run desktop
```

开发模式：

```powershell
npm run dev
```

桌面端默认连接 `http://127.0.0.1:8000`。前端不直接读取 SQLite 文件，只调用 FastAPI。

桌面端顶部不显示“服务正常”类常驻状态。只有后端连接失败时才显示简短提示，并提供重试和设置入口；提示不展示 URL、IP 或端口。

## 一键启动脚本

```powershell
cd E:\my_software\chatbot
scripts\runtime\run_app.ps1
```

或双击：

```text
scripts/runtime/run_app.bat
```

脚本只检查 Conda 和后端依赖，然后启动 FastAPI。它不会检查 Docker，也不会启动数据库容器。

## 本地用户

项目是本地单用户模式，不需要注册、登录、密码或 JWT。后端启动或首次调用 `/auth/me` 时会确保 `users` 表里存在一个默认本地用户：

- 如果 SQLite 中没有用户，自动创建默认用户。
- 如果已有且只有一个用户，直接复用。
- 如果有多个用户，抛出明确错误，避免随意选择导致旧数据关联错乱。

用户可以通过设置页修改显示 ID / 用户名，也可以上传本地头像。数据库主键 `users.id` 不建议修改。

## 主要接口

本地用户：

```text
GET  /auth/status
GET  /auth/me
PUT  /auth/me
POST /auth/me/avatar
POST /auth/logout
```

聊天：

```text
POST /chat/text
POST /chat
GET  /chat/sessions
GET  /chat/sessions/{session_id}/turns
PATCH /chat/sessions/{session_id}
POST /chat/sessions/{session_id}/archive
POST /chat/sessions/{session_id}/unarchive
```

聊天支持多个会话。新对话不会立即写入数据库，用户发送第一条消息时才创建会话；标题来自第一条用户消息，不调用 LLM。会话支持搜索、重命名、归档和恢复。归档不会删除消息，归档会话默认只读，恢复后才能继续发送。

聊天、日记和日程共用当前角色选择。前端只在 localStorage 保存已选角色 ID，真实角色列表始终来自后端 `/characters`。聊天发送时必须使用当前选中角色；历史会话按自身 `character_id` 同步角色。用户在已有会话中切换角色时，前端会开启新对话，避免把不同角色混入同一历史会话。日记页“让角色读这篇日记”也使用当前选中角色并开启新对话。日程数据不按角色隔离，角色选择只用于保持全局上下文一致。

日记：

```text
GET    /diary/entries
POST   /diary/entries
GET    /diary/entries/{entry_id}
PUT    /diary/entries/{entry_id}
DELETE /diary/entries/{entry_id}
POST   /diary/entries/{entry_id}/images
DELETE /diary/images/{image_id}
```

日程：

```text
GET    /schedule/items
POST   /schedule/items
GET    /schedule/items/{item_id}
PUT    /schedule/items/{item_id}
DELETE /schedule/items/{item_id}
GET    /schedule/today
GET    /schedule/calendar
POST   /schedule/occurrences/{occurrence_id}/complete
POST   /schedule/occurrences/{occurrence_id}/skip
POST   /schedule/occurrences/{occurrence_id}/postpone
```

日程第一阶段 MVP 使用 `schedule_items`、`schedule_occurrences`、`schedule_completion_logs` 三张 SQLite 表。延期会把旧 occurrence 标记为 `postponed`，再创建新的 `pending` occurrence；计划、自动复习、AI 排程、系统通知和聊天集成属于后续阶段。日程默认不进入聊天 prompt。

桌面端日程筛选默认收起在“筛选”入口中，不常驻展示全部类型和全部状态；页面主体只显示当前有效筛选摘要、今日任务、月历和任务详情。

人设编辑：

```text
POST /feedback/persona/turn
GET  /feedback/persona/{character_id}
POST /characters/{character_id}/persona-review/chat
POST /characters/{character_id}/persona-review/finalize
POST /characters/{character_id}/persona-review/apply
POST /characters/{character_id}/persona-review/rollback
```

桌面端聊天页提供“人设修正”入口。用户从当前会话选择真实聊天轮次，保存逐轮 persona feedback，再与人设编辑 AI 讨论修改方向。人设编辑 AI 使用独立 `PERSONA_EDITOR_*` 配置，不写入普通聊天历史、不进入长期记忆或关系记忆。`finalize` 只生成预览和字段差异；只有用户确认“确认应用修改”后才调用 `apply` 写入角色人设。`rollback` 只恢复该角色最近一次已应用修改的备份。人设修正只影响后续回复，不改写历史聊天记录。

## 人设和记忆

固定核心人设：`id`、`display_name`、`core_personality`、`speaking_style`、`relationship_to_user`、`forbidden`、`reply_patterns`、`lore`、`style_contract`。这部分不可被人设编辑 AI 自动修改、删除、覆盖或压缩，每次聊天 prompt 必须完整读取。`avatar_url` 和 `voice` 是受保护元数据。

可变补充人设：`dialogues`、`reactions`、`bad_examples`、`evaluation_criteria`、`revision_notes`。这些字段可由人设编辑 AI 少量追加，并在用户确认应用后压缩和归档。

字段上限：`dialogues=20`、`reactions=20`、`bad_examples=20`、`evaluation_criteria=30`、`revision_notes=20`。生成 preview 不写归档，只有用户确认应用并真正写入 `character.json` 后才归档到角色包 `backups/persona_compaction_archive.jsonl`。

记忆分为 pinned / always_read、普通 active、短期记忆。pinned 或 `read_policy=always` 每次 prompt 必读，不参与 topK；普通 active 记忆按相关性和重要度 topK 进入 prompt；过期、archived、superseded、deleted 或 `read_policy=never` 的记忆不会进入 prompt。

## 轻量检查

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m compileall .
```

```powershell
cd E:\my_software\chatbot\frontend\desktop
npm run build
```

## 更多文档

- [架构说明](docs/ARCHITECTURE.md)
- [Codex 协作指南](docs/CODEX_GUIDE.md)
- [桌面端前端设计](docs/桌面端前端设计.md)
- [第三方开源声明](THIRD_PARTY_NOTICES.md)
