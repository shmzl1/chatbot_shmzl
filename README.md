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
      legacy_postgres_migrations/
    main.py
    modules/
    scripts/
      migrate_postgres_to_sqlite.py
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
DATABASE_BACKEND="sqlite"
APP_DATA_DIR="./data"
SQLITE_DB_PATH="./data/chatbot.db"
UPLOAD_DIR="./data/uploads"
BACKUP_DIR="./data/backups"
```

后端启动时会自动创建 `backend/data/`、`backend/data/chatbot.db`、`backend/data/uploads/` 和 `backend/data/backups/`，并执行 `backend/database/sqlite_migrations/` 中尚未执行的迁移。

旧 PostgreSQL 迁移文件已移动到 `backend/database/legacy_postgres_migrations/`，只作为旧版本数据迁移参考，不参与默认启动。

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

脚本只检查 Conda 和后端依赖，然后启动 FastAPI。它不会启动 Docker，也不会启动 PostgreSQL/Adminer。

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

## 旧 PostgreSQL 数据迁移

一次性迁移脚本：

```text
backend/scripts/migrate_postgres_to_sqlite.py
```

迁移前请先备份旧 PostgreSQL，例如使用旧环境中的 `pg_dump`：

```powershell
pg_dump "postgresql://chatbot:change_me_local_only@127.0.0.1:5432/role_chatbot" -Fc -f E:\my_software\chatbot\backup-role-chatbot.dump
```

迁移命令：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python scripts\migrate_postgres_to_sqlite.py --postgres-url "postgresql://chatbot:change_me_local_only@127.0.0.1:5432/role_chatbot" --sqlite-path "data\chatbot.db"
```

迁移脚本不会删除或修改旧 PostgreSQL 数据。若目标 SQLite 已有数据，默认停止；确认后可加 `--overwrite`，脚本会先备份现有 SQLite 文件。

迁移脚本需要可选依赖：

```powershell
python -m pip install "psycopg[binary]"
```

这个依赖只用于旧数据迁移，不是普通启动依赖。

## 可选清理旧 Docker/PostgreSQL

只有在确认 SQLite 迁移成功、旧聊天/日记/图片/记忆都能在桌面端看到之后，才可以手动清理旧 PostgreSQL 容器和卷。项目已删除默认 `deploy/docker/docker-compose.yml`，以下命令只适用于你仍保留旧版本 compose 文件的工作副本：

```powershell
cd E:\my_software\chatbot
docker compose -f deploy\docker\docker-compose.yml down
```

删除旧数据卷有不可逆风险：

```powershell
docker compose -f deploy\docker\docker-compose.yml down -v
```

`down -v` 会删除 PostgreSQL 数据卷，执行后旧数据库数据不可恢复。

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
- [旧 PostgreSQL 迁移说明](docs/旧PostgreSQL迁移.md)
- [第三方开源声明](THIRD_PARTY_NOTICES.md)
