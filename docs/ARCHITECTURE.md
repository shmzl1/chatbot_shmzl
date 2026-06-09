# 架构说明

后端运行入口是 `backend/main.py`，路由注册来自 `backend/modules/*`。角色相关能力的唯一入口是 `backend/modules/characters`。

根目录只保留入口文档和项目级配置，不放运行脚本和 compose 文件。

## 项目结构

```text
chatbot/
  AGENTS.md
  .editorconfig
  README.md
  .gitignore
  backend/
    .env.example
    main.py
    modules/
  frontend/
    simple_web/
  docs/
    ARCHITECTURE.md
    CODEX_GUIDE.md
    计划书.md
  scripts/
    runtime/
  deploy/
    docker/
      docker-compose.yml
```

`docs/计划书.md` 是计划书唯一位置。`backend/.env.example` 是 env 示例唯一位置。`deploy/docker/docker-compose.yml` 是 Docker Compose 唯一位置。`scripts/runtime/` 是启动/暂停脚本位置。

`backend/requirements.txt` 是 Python 后端依赖文件唯一位置。根目录不保留 `requirements.txt`。

依赖安装命令：

```powershell
cd E:\my_software\chatbot
conda activate 3-chatbot
python -m pip install -r backend\requirements.txt
```

## 运行辅助文件布局

- `deploy/docker/docker-compose.yml`：PostgreSQL/Adminer。
- `scripts/runtime/run_app.*`：辅助启动。
- `scripts/runtime/暂时暂停Chatbot.bat`：停止端口并执行带 `--project-directory` 和 `-f` 参数的 Compose stop，保留数据。
- `scripts/runtime/彻底停止Chatbot.bat`：停止端口、执行带 `--project-directory` 和 `-f` 参数的 Compose stop、`wsl --shutdown`，保留数据。

Docker Compose 命令统一使用：

```powershell
docker compose --project-directory . -f deploy/docker/docker-compose.yml ...
```

## 数据流

普通聊天：

```text
frontend
  -> modules.chat.api
  -> modules.characters.service
  -> retrieval / long_term_memories / relationship_memory / chat LLM profile
  -> database
```

关系记忆：

```text
frontend
  -> modules.relationship_memory.api
  -> modules.relationship_memory.service
  -> relationship_memory_events
```

人设编辑：

```text
frontend
  -> characters persona-review endpoints
  -> modules.persona_review.service
  -> persona_editor LLM profile
  -> patch
  -> preview_character_json
  -> user confirmed apply
  -> modules.characters validation and write
```

语音：

```text
frontend
  -> modules.voice.api or chat voice option
  -> services.tts_service
  -> GPT-SoVITS /tts
```

## LLM

普通聊天只读取 `CHAT_*`，人设编辑只读取 `PERSONA_EDITOR_*`。两个 profile 都只允许 provider 为 `openai`。

项目不读取旧 `OPENAI_*` 配置，不读取 `LLM_PROVIDER`，不允许 `auto`、`mock` 或 `fallback`。缺配置、模型失败、超时和 JSON 非法都会直接暴露为错误。

## JSON

LLM JSON 使用严格 `json.loads`。后端不会从 Markdown 代码块或自然语言中截取 JSON，也不会自动修补非法 JSON。

## 关系记忆

`relationship_memory_events` 是关系长期上下文的最小闭环表。普通聊天会读取当前角色有效关系记忆并加入 prompt，但保留旧 `long_term_memories` 路径兼容。

用户确认聊天中的记忆建议时，前端继续写入 `/memory`，同时写入 `/relationship-memory`。停用关系记忆通过 `is_active = false` 完成，不删除历史事件。

## GPT-SoVITS

`neutral` 是默认语音参考。没有明确选择 emotion 时使用 `neutral`。明确选择其他 emotion 时必须存在对应参考音频，缺失就报错。`prompt_text` 可以为空。
