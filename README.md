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
```

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

人设编辑：

```text
POST /characters/{character_id}/persona-review/chat
POST /characters/{character_id}/persona-review/finalize
POST /characters/{character_id}/persona-review/apply
POST /characters/{character_id}/persona-review/rollback
```

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
