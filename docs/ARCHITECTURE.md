# 架构说明

后端运行入口是 `backend/main.py`，路由注册来自 `backend/modules/*`。角色相关能力的唯一入口是 `backend/modules/characters`。

根目录只保留入口文档和项目级配置，不放运行脚本和 compose 文件。

## 项目结构

```text
chatbot/
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
  -> retrieval / memory / chat LLM profile
  -> database
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

## GPT-SoVITS

`neutral` 是默认语音参考。没有明确选择 emotion 时使用 `neutral`。明确选择其他 emotion 时必须存在对应参考音频，缺失就报错。`prompt_text` 可以为空。
