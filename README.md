# 虚拟人物陪伴系统

本项目是本地运行的虚拟人物聊天系统。运行入口集中在 `backend/modules/*`，角色读取、校验、头像和角色包管理都走 `backend/modules/characters`。

## 当前结构

```text
chatbot/
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

## 启动

启动数据库：

```powershell
cd E:\my_software\chatbot
docker compose --project-directory . -f deploy/docker/docker-compose.yml up -d postgres adminer
```

启动后端：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

辅助启动脚本：

```text
scripts/runtime/run_app.bat
scripts/runtime/run_app.ps1
```

暂停数据库并保留数据：

```powershell
cd E:\my_software\chatbot
docker compose --project-directory . -f deploy/docker/docker-compose.yml stop
```

辅助暂停脚本：

```text
scripts/runtime/暂时暂停Chatbot.bat
scripts/runtime/彻底停止Chatbot.bat
```

`暂时暂停Chatbot.bat` 会停止端口并执行带 `--project-directory` 和 `-f` 参数的 Compose stop，保留数据。`彻底停止Chatbot.bat` 还会执行 `wsl --shutdown` 释放 WSL/Docker 内存，但不执行 `docker compose down`，不执行 `docker compose down -v`，不删除 PostgreSQL volume。

## 接口路径

普通聊天接口路径保持不变：

```text
POST /chat/text
POST /chat
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

`apply` 必须由用户确认后才写入。patch 不允许修改 `id`、`display_name`、`avatar_url`、`voice`、`gptsovits_base_url`、`ref_audio_path`、`prompt_text`。模型返回非法 JSON 时直接返回 502，不做自动修补。

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
