# Local Role Voice Chatbot

## 后端模块结构

后端开始采用 `backend/modules` 按功能域组织代码。当前是兼容式迁移：
旧的 `backend/api` 和 `backend/services` 仍然保留，已有功能先通过
`modules/{feature}/api.py` wrapper 接入，避免一次性移动大量业务代码。

当前主应用从这些模块导入 router：

```text
modules.health.api
modules.auth.api
modules.characters.api
modules.chat.api
modules.debug.api
modules.persona_review.api
modules.knowledge.api
modules.memory.api
modules.voice.api
```

新功能优先新增到 `backend/modules/{feature}/`，再逐步拆出该功能自己的
`api.py`、`service.py`、`repository.py` 和 `schemas.py`。不要继续把新功能
直接塞进旧的 `backend/api` 或 `backend/services`。

`schedule` 和 `diary` 目前只是预留模块，还没有业务实现，也没有在
`backend/main.py` 中注册 router。

## 功能域与共享关系记忆

`chat`、`schedule`、`diary` 是三个独立业务功能：

- `chat` 保存自由聊天会话和消息。
- `schedule` 未来保存日程计划、日程项、日程复盘和日程反馈。
- `diary` 未来保存日记、日记阅读会话和日记阅读对话。

它们不共享业务会话表。`schedule` 和 `diary` 不能写入
`chat_sessions` 或 `chat_turns`，也不能互相依赖。

但用户不是在和三个互不认识的工具交互，而是在不同场景里和同一个角色交流。
因此三类功能未来可以通过 `relationship_memory` 共享“同一个角色对用户的长期理解”。

`relationship_memory` 不是普通聊天表，不是日程表，也不是日记表。它保存的是：

```text
某个角色对用户的长期理解
```

未来写入方向：

- `chat` 从普通聊天中提取用户偏好、边界、情绪状态和长期习惯。
- `schedule` 从日程安排和复盘中提取拖延模式、压力来源和任务习惯。
- `diary` 从日记阅读中提取近期生活事件、孤独感、情绪变化和关注点。

未来读取方向：

- `chat` 生成回复时读取 `relationship_memory`。
- `schedule` 生成日程反馈时读取 `relationship_memory`。
- `diary` 进行日记阅读对话时读取 `relationship_memory`。

这样可以做到业务数据隔离，同时让同一个角色在不同场景里延续对用户的理解。

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
    data/                  角色包、示例资料、上传目录
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
LLM_PROVIDER="openai"
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

启动前先安装依赖并运行后端：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

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

收尾安全验证：
- `.env` 中缺少 `OPENAI_API_KEY`、`OPENAI_MODEL` 或 `OPENAI_BASE_URL` 时，聊天接口应该显示明确配置错误，不自动 mock。
- 角色包缺少 `character.json`、JSON 格式错误或 `lore/dialogues/reactions` 字段错误时，后端应该显示具体文件路径。
- 上传头像真实文件保存在 `backend/data/uploads/`，不会被提交到 Git；只保留 `.gitkeep` 目录占位文件。

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

当前项目优先本地调试，默认关闭静默兜底。配置错误、数据库错误、migration 错误、模型调用错误、角色包错误、知识库 JSONL 错误、语音服务错误会直接暴露，方便定位问题。

- 数据库不可用时，聊天和会话接口会返回明确数据库错误，不返回空数据。
- LLM_PROVIDER 默认使用 `openai`。`LLM_PROVIDER=auto` 不会自动切换 mock；`OPENAI_API_KEY`、`OPENAI_MODEL`、`OPENAI_BASE_URL` 缺失或模型接口失败时，聊天接口会直接报错，前端显示后端返回的 detail。
- 角色包 `character.json` 缺失、JSON 格式错误或字段格式错误会报具体文件路径。
- `voice=true` 且 GPT-SoVITS 不可用时会返回语音服务错误；`voice=false` 仍可只走文本。
- 前端会优先显示后端返回的 `detail`；如果没有 `detail`，会显示 HTTP 状态码和接口路径。

如果以后需要演示模式，可以单独增加 `DEMO_MODE=true`，但默认不启用。

## 如何新增角色

推荐使用角色包。新增角色只需要维护一个 `character.json`：

```text
backend/data/character_packs/{character_id}/character.json
```

1. 生成角色包：

```powershell
cd backend
python -m tools.character_pack new asa_mitaka --name "三鹰朝"
```

2. 编辑角色配置：

```text
backend/data/character_packs/asa_mitaka/character.json
```

3. 校验角色包：

```powershell
python -m tools.character_pack validate asa_mitaka
```

4. 启动后端并打开网页：

```text
http://127.0.0.1:8000/app/
```

5. 如果角色没有出现，打开 debug 接口查看错误：

```text
http://127.0.0.1:8000/debug/characters
```

说明：

- 新角色只需要维护一个 `character.json`。
- 不再推荐手动创建 `lore/dialogues/reactions` 分散 JSONL 文件。
- 语音文件放在角色包自己的 `voice_refs` 目录，例如 `backend/data/character_packs/asa_mitaka/voice_refs/neutral/ref_001.wav`。
- 语音 `wav`、模型权重、头像素材不要提交到 GitHub。
- 角色头像仍可以在网页里上传。

## 人设反馈与自动修正

聊天页面里，每条角色回复旁边都有“选中用于人设修改”按钮。选中一条或多条回复后，可以在人设修改工作台里输入评价、点击常用标签组合评价，再决定是否保存反馈或发送给人设编辑 AI。保存反馈会写入 `persona_turn_feedback`，不会立刻修改角色文件。

新版网页里，这部分升级为“人设修改工作台”：

1. 在左侧角色信息卡附近点击“打开人设编辑”，打开独立的人设编辑抽屉。
2. 在聊天记录里点击某条角色回复旁边的“选中用于人设修改”。
3. 可以选择一条或多条回复，选中后消息会高亮，并出现在工作台的“当前选中的对话列表”里。
4. 在评价输入框里写评价，例如“这句太像 AI 了，不像三鹰朝，应该更别扭一点”。
5. 点击预设标签只会把标签文字追加到评价输入框，不会提交、不保存、不修改文件。
6. 点击“保存这条反馈”会把当前评价保存到 `persona_turn_feedback`。
7. 点击“发送给人设编辑 AI”会调用编辑对话接口，和一个独立的人设编辑 AI 多轮讨论怎么改。
8. 不满意可以继续补充要求，再发给人设编辑 AI。
9. 点击“生成最终修改方案”后，后端只生成最终方案和 `preview_character_json`。
10. 预览确认无误后，点击“确认应用修改”，才会写入 `character.json`。
11. 如果不满意，可以点击“回滚上一版人设”恢复固定备份。

人设编辑 AI 不是当前聊天角色。它只负责分析回复、整理反馈、提出修改方案；它不会假装自己是角色，也不会把人设编辑对话写入普通 `chat_sessions`。

查看当前角色反馈统计：

```text
GET /feedback/persona/{character_id}
```

人设编辑抽屉里的反馈统计区域会显示总反馈数、good / bad / neutral 数量、最近 issue_tags 统计、是否存在可回滚备份和上次修改摘要。也可以用：

```text
GET /debug/characters/{character_id}
```

查看 `character.json` 是否合法、`style_contract` / `evaluation_criteria` 是否存在、`bad_examples` 和 `revision_notes` 数量、人设反馈数量、上一版备份是否存在，以及最近一次修改摘要。

生成 AI 修改建议：

```text
POST /characters/{character_id}/persona-review/summarize
```

这个接口只生成建议和 `preview_character_json`，不会写入文件。反馈少于 5 条时，只建议轻量修改，不建议大改。

人设修改工作台使用的多轮编辑接口：

```text
POST /characters/{character_id}/persona-review/chat
```

这个接口只返回人设编辑 AI 的讨论回复和前端可继续保存的 `history`，不写入文件。

生成最终修改方案：

```text
POST /characters/{character_id}/persona-review/finalize
```

这个接口根据选中的对话、用户评价、多轮编辑历史、已保存反馈统计和当前 `character.json` 生成最终方案。它也只返回 `preview_character_json`，不写入文件。

用户确认后应用修改：

```text
POST /characters/{character_id}/persona-review/apply
```

应用前会把当前文件备份为：

```text
backend/data/character_packs/{character_id}/backups/character.previous.json
```

每个角色最多只保留上一版备份。多次应用会覆盖更早的 `character.previous.json`。如果想长期保存某个版本，需要手动把 `character.json` 复制到别处。

回滚上一版：

```text
POST /characters/{character_id}/persona-review/rollback
```

回滚前会检查上一版备份是否存在、JSON 是否合法、`id` 是否匹配、角色包校验是否通过。校验失败不会覆盖当前 `character.json`。

AI 自动修改时优先允许改：

- `style_contract`
- `speaking_style`
- `forbidden`
- `dialogues`
- `reactions`
- `bad_examples`
- `evaluation_criteria`
- `revision_notes`

禁止 AI 自动改：

- `id`
- `display_name`
- `avatar_url`
- `voice`
- `gptsovits_base_url`
- `ref_audio_path`
- `prompt_text`

不建议反馈很少时频繁修改人设。更稳的做法是先积累几条明确反馈，再生成修改建议，预览无误后再确认应用。

## 注意事项

- 不要提交 `backend/.env`、根目录 `.env` 或任何 `.env.*` 本地配置。
- 不要提交真实 API Key、数据库密码、Token、JWT 密钥、私钥文件。
- `.env.example` 只能写变量名和假示例值。
- 上传前检查截图、日志、数据库导出、语音素材和临时文件，避免包含私人信息。
