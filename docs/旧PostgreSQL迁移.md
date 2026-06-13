# 旧 PostgreSQL 迁移到 SQLite

项目默认数据库已经迁移为 SQLite，普通启动不再需要 Docker、PostgreSQL 或 Adminer。旧 PostgreSQL 数据不会被自动删除。

## 1. 备份旧 PostgreSQL

在确认旧数据库还能访问时先备份：

```powershell
pg_dump "postgresql://chatbot:change_me_local_only@127.0.0.1:5432/role_chatbot" -Fc -f E:\my_software\chatbot\backup-role-chatbot.dump
```

## 2. 安装迁移脚本可选依赖

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m pip install "psycopg[binary]"
```

`psycopg` 只用于旧数据迁移，不是普通启动依赖。

## 3. 执行迁移

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python scripts\migrate_postgres_to_sqlite.py --postgres-url "postgresql://chatbot:change_me_local_only@127.0.0.1:5432/role_chatbot" --sqlite-path "data\chatbot.db"
```

脚本会迁移 users、聊天、日记、图片元数据、长期记忆、关系记忆、人设反馈、知识库和角色头像映射等业务表，并保留原始 id。

若目标 SQLite 已有数据，默认停止。确认备份后可使用：

```powershell
python scripts\migrate_postgres_to_sqlite.py --postgres-url "postgresql://chatbot:change_me_local_only@127.0.0.1:5432/role_chatbot" --sqlite-path "data\chatbot.db" --overwrite
```

`--overwrite` 会先备份已有 SQLite 文件，再重建目标文件。

## 4. 验证 SQLite

确认文件存在：

```powershell
Test-Path E:\my_software\chatbot\backend\data\chatbot.db
```

不启动 Docker，直接启动后端：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000/docs
```

验证：

```text
GET /auth/me
GET /diary/entries
POST /chat/text
```

日记图片应继续通过 `/uploads/...` URL 访问。图片文件本身不会由迁移脚本复制；如果旧图片不在 `backend/data/uploads/` 下，请手动把旧 uploads 内容复制到新的 uploads 目录。

## 5. 可选清理旧 Docker/PostgreSQL

只有在确认 SQLite 迁移成功、旧数据都能在桌面端看到之后，才可以删除旧 PostgreSQL 容器和卷。

项目已删除默认 `deploy/docker/docker-compose.yml`。如果你的旧工作副本里仍保留该文件，可以执行：

```powershell
cd E:\my_software\chatbot
docker compose -f deploy\docker\docker-compose.yml down
```

删除数据卷风险很高：

```powershell
docker compose -f deploy\docker\docker-compose.yml down -v
```

`down -v` 会删除 PostgreSQL 数据卷，执行后旧数据库数据不可恢复。
