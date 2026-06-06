# Local Role Voice Chatbot

## 项目简介

这是一个本地角色聊天机器人项目，用于调试角色卡、长期记忆、知识库检索、OpenAI 兼容模型接入、用户头像和角色头像展示。登录功能是本地单用户登录锁，只用于防止别人坐到你的电脑前直接打开 `http://127.0.0.1:8000/app/` 使用你的 chatbot；它不是公开网站级安全系统，也不包含多用户、管理员、找回密码或邮箱验证。

## 技术栈

- 后端：Python、FastAPI、Uvicorn、Pydantic
- 数据库：PostgreSQL、psycopg
- 认证：JWT、Argon2id 密码哈希
- 前端：HTML、CSS、原生 JavaScript
- 本地服务：Docker Compose、Adminer
- AI 接入：OpenAI 兼容 Chat Completions API

## 目录结构

```text
chatbot/
  backend/                 FastAPI 后端
    api/                   接口路由
    core/                  配置、Schema、安全工具
    services/              LLM、数据库、认证、头像、记忆、知识库等服务
    data/                  角色卡、示例资料、上传目录
    requirements.txt       后端依赖
    .env.example           后端环境变量示例
  frontend/simple_web/     浏览器前端
  docker-compose.yml       PostgreSQL 和 Adminer
  run_app.bat              Windows 一键启动脚本
  run_app.ps1              PowerShell 一键启动脚本
  .env.example             根目录环境变量示例
  .gitignore               Git 忽略规则
  README.md                项目说明
```

## 安装后端依赖

```powershell
cd backend
python -m pip install -r requirements.txt
```

如果你使用本地 Conda 环境，可以先执行：

```powershell
conda activate 3-chatbot
```

## 环境变量配置

首次运行前复制示例配置：

```powershell
copy .env.example backend\.env
```

然后编辑 `backend/.env`，填写自己的数据库连接、模型配置和本地 JWT 密钥。不要把真实 API Key、数据库密码、Token 或私钥提交到 GitHub。

常用变量：

```text
DATABASE_URL="postgresql://your_db_user:your_db_password@127.0.0.1:5432/your_db_name"
LLM_PROVIDER="auto"
OPENAI_API_KEY="your_api_key_here"
OPENAI_BASE_URL="https://your-openai-compatible-base-url.example.com/api/v3"
OPENAI_MODEL="your_model_name_here"
JWT_SECRET_KEY="change_this_to_a_long_random_string"
JWT_EXPIRE_MINUTES="10080"
UPLOAD_DIR="./data/uploads"
AVATAR_MAX_SIZE_MB="5"
```

`OPENAI_BASE_URL` 填基础地址，不要带 `/chat/completions`。如果你用 Docker Compose 自定义 PostgreSQL 账号密码，也可以把 `.env.example` 复制为根目录 `.env`，再修改 `POSTGRES_DB`、`POSTGRES_USER`、`POSTGRES_PASSWORD`。

## 启动方式

推荐使用根目录的一键脚本：

```powershell
.\run_app.ps1
```

或手动启动：

```powershell
cd E:\my_software\chatbot
docker compose up -d

cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：

```text
http://127.0.0.1:8000/app/
```

数据库管理页面：

```text
http://127.0.0.1:8081
```

Adminer 登录信息以你本地 `.env` 或 `docker-compose.yml` 中的 PostgreSQL 配置为准。

## 本地单用户登录锁

第一次访问 `/app/` 时，前端会请求 `GET /auth/status`。如果数据库里还没有本地用户，会显示“初始化本地账号”页面，你只需要设置一个用户名和密码。创建成功后会自动登录。

本地登录密码不会明文保存。后端使用 Argon2id 生成 `password_hash`，支持较长密码、中文密码和符号密码，不再使用 bcrypt 直接处理原始密码，也不再受 bcrypt 72 bytes 限制。为了防止极端输入，当前只限制密码最多 1024 个字符。

以后再访问时：

- 有效 token 存在于浏览器 `localStorage` 时，刷新页面会保持登录。
- 没有 token 时显示登录页面。
- token 无效或过期时会自动清除 token，并提示“登录已失效，请重新登录”。
- 初始化后不会再显示普通注册入口。

受登录保护的主要功能：

- 发送聊天消息：`POST /chat/text`、`POST /chat`
- 查看、删除历史会话：`/debug/sessions...`
- 新增、查看、删除长期记忆：`/memory...`
- 新增、查看、删除知识库：`/knowledge...`
- 上传用户头像：`POST /auth/me/avatar`
- 上传角色头像：`POST /characters/{character_id}/avatar`

部分本地开发调试接口如 `/debug/database`、`/debug/export` 暂未强制保护，只建议在本机开发时使用。

## 头像上传

用户头像：

- 登录后点击左侧“上传我的头像”
- 接口：`POST /auth/me/avatar`
- 保存目录：`backend/data/uploads/avatars/user/`
- 返回 `avatar_url`

角色头像：

- 登录后选择角色，点击“上传角色头像”
- 接口：`POST /characters/{character_id}/avatar`
- 保存目录：`backend/data/uploads/avatars/characters/`
- 角色 JSON 会保存 `avatar_url`，刷新页面后仍然显示

上传限制：

- 仅允许 `png`、`jpg`、`jpeg`、`webp`
- 默认最大 5MB
- 文件名使用安全生成名，不使用用户上传的原始文件名
- 浏览器可直接访问 `/uploads/...` URL
- 真实上传文件已被 `.gitignore` 忽略

## 新增接口

```text
GET  /auth/status
POST /auth/setup
POST /auth/login
GET  /auth/me
POST /auth/me/avatar
POST /auth/logout
POST /characters/{character_id}/avatar
```

## 验收流程

1. 打开 `http://127.0.0.1:8000/app/`
2. 第一次看到“初始化本地账号”页面
3. 设置本地用户名和密码
4. 进入聊天页面
5. 上传“我的头像”
6. 上传“角色头像”
7. 发送一条聊天消息
8. 确认用户消息显示用户头像，角色回复显示角色头像
9. 刷新页面，确认仍保持登录和头像
10. 点击退出登录，确认不能直接进入聊天页面
11. 重新登录，确认聊天功能正常

## 重置本地数据

如果你想彻底重置数据库和本地账号，可以执行：

```powershell
docker compose down -v
docker compose up -d
```

注意：`down -v` 会删除 PostgreSQL 数据卷，也就是聊天记录、长期记忆、知识库、本地用户都会被删除。

## 数据库更新与数据保留

普通更新代码后，不需要删除 Docker volume。后端启动时会自动连接 PostgreSQL，创建 `schema_migrations` 表，并按文件名顺序执行 `backend/database/migrations/` 里尚未应用的 SQL migration。

迁移规则：

- `schema_migrations.version` 是主键，同一版本只会记录一次。
- migration 文件必须幂等，使用 `CREATE TABLE IF NOT EXISTS`、`ALTER TABLE ADD COLUMN IF NOT EXISTS`、`CREATE INDEX IF NOT EXISTS`。
- 默认数据或映射数据必须使用唯一约束配合 `ON CONFLICT DO NOTHING` 或 `ON CONFLICT DO UPDATE`。
- 普通迁移不会删除 `chat_sessions`、`chat_turns`、`long_term_memories`、`knowledge_items`、`turn_feedback` 或本地用户。
- 程序自动迁移禁止使用 `DROP TABLE`、`DROP DATABASE`、`TRUNCATE` 和清空核心数据表的 SQL。
- 如果 migration 失败，后端启动会失败并显示具体 migration 文件名和 SQL 错误原因，不会自动删表、重建表或清空数据。

后续更新数据库结构时，通常只需要：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

不要随便执行：

```powershell
docker compose down -v
```

`down -v` 会删除 PostgreSQL volume，导致聊天记录、长期记忆、知识库、本地用户全部丢失。

备份数据库：

```powershell
docker exec -t role-chatbot-postgres pg_dump -U chatbot -d role_chatbot > backup_role_chatbot.sql
```

恢复数据库：

```powershell
Get-Content .\backup_role_chatbot.sql | docker exec -i role-chatbot-postgres psql -U chatbot -d role_chatbot
```

## 错误暴露策略

当前项目优先本地调试，默认关闭静默兜底。配置错误、数据库错误、migration 错误、模型调用错误、角色文件错误、知识库 JSONL 错误、语音服务错误会直接暴露，方便定位问题。

- 数据库不可用时，聊天和会话接口会返回明确数据库错误，不返回空数据。
- LLM 配置不完整或接口失败时，聊天接口会报错，不自动切换 mock 回复。
- 角色 JSON、检索 JSONL 格式错误会报具体文件和行号。
- `voice=true` 且 GPT-SoVITS 不可用时会返回语音服务错误；`voice=false` 仍可只走文本。
- 前端会优先显示后端返回的 `detail`；如果没有 `detail`，会显示 HTTP 状态码和接口路径。

如果以后需要演示模式，可以单独增加 `DEMO_MODE=true`，但默认不启用。

## 注意事项

- 不要提交 `backend/.env`、根目录 `.env` 或任何 `.env.*` 本地配置。
- 不要提交真实 API Key、数据库密码、Token、JWT 密钥、私钥文件。
- `.env.example` 只能写变量名和假示例值。
- 上传前检查截图、日志、数据库导出、语音素材和临时文件，避免包含私人信息。
