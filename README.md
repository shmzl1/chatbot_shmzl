# 虚拟人物陪伴系统

本项目是本地运行的虚拟人物聊天系统。运行入口集中在 `backend/modules/*`，角色读取、校验、头像和角色包管理都走 `backend/modules/characters`。

## 当前结构

```text
chatbot/
  AGENTS.md
  .editorconfig
  README.md
  .gitignore
  backend/
    .env.example
    main.py
    requirements.txt
    core/
    modules/
    services/
    database/
  frontend/
    simple_web/
  docs/
    ARCHITECTURE.md
    CODEX_GUIDE.md
    计划书.md
  scripts/
    runtime/
      run_app.bat
      run_app.ps1
      暂时暂停Chatbot.bat
      彻底停止Chatbot.bat
  deploy/
    docker/
      docker-compose.yml
```

根目录只保留入口文档和项目级配置，不放运行脚本、Docker Compose 文件或环境变量示例。

## 环境变量

唯一 env 示例是 `backend/.env.example`。本地真实配置放在 `backend/.env`：

```powershell
Copy-Item backend/.env.example backend/.env
```

普通聊天只读取 `CHAT_*`：

```env
CHAT_LLM_PROVIDER="openai"
CHAT_OPENAI_API_KEY=""
CHAT_OPENAI_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
CHAT_OPENAI_MODEL="doubao-seed-character-251128"
CHAT_OPENAI_TIMEOUT_SECONDS="120"
CHAT_OPENAI_TEMPERATURE="0.8"
```

人设编辑只读取 `PERSONA_EDITOR_*`：

```env
PERSONA_EDITOR_LLM_PROVIDER="openai"
PERSONA_EDITOR_OPENAI_API_KEY=""
PERSONA_EDITOR_OPENAI_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
PERSONA_EDITOR_OPENAI_MODEL="doubao-seed-2-0-pro-260215"
PERSONA_EDITOR_OPENAI_TIMEOUT_SECONDS="180"
PERSONA_EDITOR_OPENAI_TEMPERATURE="0.2"
```

项目不保留旧 `OPENAI_*`，不允许 `LLM_PROVIDER`、`auto`、`mock` 或 `fallback`。缺配置、模型失败、JSON 非法都会直接报错。

## 后端依赖

Python 后端依赖文件唯一位置是 `backend/requirements.txt`，根目录不保留 `requirements.txt`。

从项目根目录安装：

```powershell
cd E:\my_software\chatbot
conda activate 3-chatbot
python -m pip install -r backend\requirements.txt
```

或进入后端目录安装：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m pip install -r requirements.txt
```

## 启动方式

本项目当前为本地单用户运行方式，主要包含：

* FastAPI 后端
* PostgreSQL 数据库
* Adminer 数据库管理页面
* `frontend/simple_web` 简单网页前端

网页入口：

```text
http://127.0.0.1:8000/app/
```

---

### 1. 首次准备环境

进入项目根目录：

```powershell
cd E:\my_software\chatbot
```

创建并激活 Conda 环境：

```powershell
conda create -n 3-chatbot python=3.10 -y
conda activate 3-chatbot
```

安装后端依赖：

```powershell
cd backend
pip install -r requirements.txt
```

---

### 2. 配置环境变量

复制环境变量示例文件：

```powershell
cd E:\my_software\chatbot
copy .env.example backend\.env
```

然后打开：

```text
backend/.env
```

至少检查并填写以下配置：

```env
DATABASE_URL="postgresql://chatbot:change_me_local_only@127.0.0.1:5432/role_chatbot"

CHAT_LLM_PROVIDER="openai"
CHAT_OPENAI_API_KEY="your_api_key_here"
CHAT_OPENAI_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
CHAT_OPENAI_MODEL="your_chat_model_here"

PERSONA_EDITOR_LLM_PROVIDER="openai"
PERSONA_EDITOR_OPENAI_API_KEY="your_api_key_here"
PERSONA_EDITOR_OPENAI_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
PERSONA_EDITOR_OPENAI_MODEL="your_persona_editor_model_here"

JWT_SECRET_KEY="change_this_to_a_long_random_string"
```

注意：

* 不要把真实 API Key 提交到 Git。
* 不要提交 `backend/.env`。
* 如果不使用人设编辑功能，也建议先把 `PERSONA_EDITOR_*` 配好，避免调用相关接口时报错。
* 本项目不使用 mock LLM。模型配置错误时会直接报错。

---

### 3. 启动数据库

回到项目根目录：

```powershell
cd E:\my_software\chatbot
docker compose --project-directory "E:\my_software\chatbot" -f "E:\my_software\chatbot\deploy\docker\docker-compose.yml" up -d postgres adminer
```

启动后：

* PostgreSQL 地址：`127.0.0.1:5432`
* 数据库名：`role_chatbot`
* 用户名：`chatbot`
* 密码：`change_me_local_only`
* Adminer 地址：`http://127.0.0.1:8081`

如果想查看容器状态：

```powershell
docker compose ps
```

---

### 4. 启动后端

进入后端目录：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

启动成功后访问：

```text
http://127.0.0.1:8000/app/
```

接口文档地址：

```text
http://127.0.0.1:8000/docs
```

健康检查地址：

```text
http://127.0.0.1:8000/health
```

---

### 5. 一键启动方式

项目根目录提供了辅助启动脚本。

PowerShell 启动：

```powershell
cd E:\my_software\chatbot
.\run_app.ps1
```

或双击：

```text
run_app.bat
```

一键启动脚本会尝试：

1. 检查 Docker；
2. 检查 Conda；
3. 检查 `3-chatbot` 环境；
4. 启动 PostgreSQL 和 Adminer；
5. 等待 PostgreSQL healthy；
6. 检查后端依赖；
7. 打开 `http://127.0.0.1:8000/app/`；
8. 启动 FastAPI 后端。

如果端口 `8000` 已被占用，脚本会认为后端可能已经在运行，并直接打开网页。

---

### 6. GPT-SoVITS 语音服务

GPT-SoVITS 语音 API 不会跟随后端自动启动。

如果只使用文字聊天，可以不启动语音服务。

如果需要语音功能，需要单独启动 GPT-SoVITS API，并保证 `.env` 中配置：

```env
GPTSOVITS_BASE_URL="http://127.0.0.1:9880"
GPTSOVITS_TIMEOUT_SECONDS="120"
```

---

### 7. 暂停和停止

临时暂停后端：

```text
暂时暂停Chatbot.bat
```

彻底停止项目相关服务：

```text
彻底停止Chatbot.bat
```

如果手动停止 Docker 数据库：

```powershell
docker compose down
```

注意：

```powershell
docker compose down -v
```

会删除数据库卷，可能导致本地聊天记录、记忆、反馈等数据丢失。一般不要执行。

普通聊天接口路径保持不变：

```text
POST /chat/text
POST /chat
```

关系记忆接口：

```text
POST /relationship-memory
GET /relationship-memory?character_id=role01
POST /relationship-memory/{event_id}/deactivate
GET /relationship-memory/debug?character_id=role01
```

人设编辑接口路径保持不变：

```text
POST /characters/{character_id}/persona-review/chat
POST /characters/{character_id}/persona-review/finalize
POST /characters/{character_id}/persona-review/apply
POST /characters/{character_id}/persona-review/rollback
```

## 人设编辑

`finalize` 只接受模型输出 patch JSON。后端把 patch 合并到当前 `character.json`，生成 `preview_character_json`，校验通过后返回预览。

`apply` 必须由用户确认后才写入。模型返回非法 JSON 时直接返回 502，不做自动修补。

人设分为两层：

- 固定核心人设：`id`、`display_name`、`core_personality`、`speaking_style`、`relationship_to_user`、`forbidden`、`reply_patterns`、`lore`、`style_contract`。这些字段不可被人设编辑 AI 自动修改、删除、覆盖或压缩，每次聊天 prompt 必须完整读取。`avatar_url` 和 `voice` 是受保护元数据，也不可被人设编辑 AI 自动修改。
- 可变补充人设：`dialogues`、`reactions`、`bad_examples`、`evaluation_criteria`、`revision_notes`。这些字段可以由人设编辑 AI 追加，并在用户确认应用后压缩和归档。

可变补充字段上限：`dialogues` 20 条，`reactions` 20 条，`bad_examples` 20 条，`evaluation_criteria` 30 条，`revision_notes` 20 条。压缩只在用户点击【确认应用修改】并真正写入 `character.json` 时发生；被裁剪内容写入角色包 `backups/persona_compaction_archive.jsonl`，不会在生成 preview 时重复归档。

## 关系记忆

`relationship_memory_events` 保存用户和角色之间的有效长期关系上下文。普通聊天仍兼容旧 `long_term_memories`，同时会把有效关系记忆加入聊天 prompt 的长期上下文。

前端“确认记忆建议”时会继续写入旧长期记忆，并额外写入一条关系记忆事件，来源标记为 `chat`，记录会话和 turn 信息。停用关系记忆只会把 `is_active` 置为 `false`，不会删除历史事件。

记忆分为三类：

- pinned / always_read 记忆：`is_pinned=true` 或 `read_policy=always`，每次 prompt 必须读取，不参与 topK 裁剪，不允许 AI 自动删除或覆盖。
- 普通 active 记忆：`status=active` 且 `read_policy=relevant`，只按相关性和重要度 topK 进入 prompt。
- 短期记忆：可以设置 `expires_at`，过期后不再进入 prompt。

`archived`、`superseded`、`deleted`、`read_policy=never` 或已过期的记忆不会进入聊天 prompt。未来前端管理界面应允许用户手动设置哪些记忆是 pinned，哪些可以归档或遗忘。

## 语音规则

GPT-SoVITS 的 `prompt_text` 可以为空。`neutral` 是默认语音参考：用户没有明确选择 emotion 时使用 `neutral`。

用户明确选择 `angry`、`sad`、`happy` 等 emotion 时，必须存在该 emotion 的参考音频；缺少对应 `ref_audio_path` 会直接报错，不自动退回 `neutral`。

## 轻量检查

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m compileall .
```

## 更多文档

- [项目计划书](docs/计划书.md)
- [架构说明](docs/ARCHITECTURE.md)
- [Codex 协作指南](docs/CODEX_GUIDE.md)
- [模块说明](backend/modules/README.md)
