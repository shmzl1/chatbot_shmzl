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
    desktop/
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

`docs/计划书.md` 是计划书唯一位置。`backend/.env.example` 是 env 示例唯一位置。`deploy/docker/docker-compose.yml` 是 Docker Compose 唯一位置。`scripts/runtime/` 是启动/暂停脚本位置。`frontend/desktop/` 是唯一前端位置，旧 `frontend/simple_web` 已删除。

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

认证与本地用户：

```text
frontend
  -> GET /auth/me
  -> services.auth_service.ensure_default_user
  -> users singleton row
```

项目是 Windows 本地单用户模式，不需要注册、登录、密码、JWT 或 Bearer Token。后端启动和首次读取 `/auth/me` 时会自动创建默认本地用户。`get_current_user` 保留为依赖函数名，但只返回默认用户。用户可通过 `PUT /auth/me` 修改显示 ID / 用户名，通过 `POST /auth/me/avatar` 上传头像。数据库主键 `users.id` 不应修改；清空用户数据需要手动清理数据库或后续工具。

前端：

```text
frontend/desktop
  -> Electron
  -> React + TypeScript + Vite
  -> Tailwind CSS / Radix UI
  -> FastAPI HTTP APIs
```

后端不再挂载 `/app/` 静态主界面。根路径 `/` 重定向到 `/docs`，主界面由 Electron 桌面端提供。`/uploads/...` 和 `/outputs/...` 仍由 FastAPI 静态挂载。

普通聊天：

```text
frontend
  -> modules.chat.api
  -> modules.characters.service
  -> retrieval / long_term_memories / relationship_memory / chat LLM profile
  -> database
```

日记：

```text
frontend diary page
  -> modules.diary.api
  -> diary_entries / diary_attachments
  -> uploads/diary/images
```

聊天默认不会读取日记。只有请求显式传入 `diary_entry_id` 时，`modules.diary.context` 才会读取当前用户的那一篇日记，并加入 prompt 的“用户主动提供的日记上下文”。日记不会自动写入长期记忆。

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

人设数据分层：

- 固定核心人设：`id`、`display_name`、`core_personality`、`speaking_style`、`relationship_to_user`、`forbidden`、`reply_patterns`、`lore`、`style_contract`。这部分只能由用户未来在管理界面中显式修改，AI 不能自动 patch，也不能被压缩裁剪。聊天 prompt 每次完整读取固定核心人设。`avatar_url` 和 `voice` 是受保护元数据，也不能被人设编辑 AI 自动修改。
- 可变补充人设：`dialogues`、`reactions`、`bad_examples`、`evaluation_criteria`、`revision_notes`。这部分允许人设编辑 AI 追加；用户确认 apply 后，后端按上限压缩，并将裁剪内容追加到角色包 `backups/persona_compaction_archive.jsonl`。

可变补充上限：`dialogues=20`、`reactions=20`、`bad_examples=20`、`evaluation_criteria=30`、`revision_notes=20`。生成 preview 不写归档，只有用户确认应用并写入 `character.json` 后才归档。

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

记忆读取分层：

- pinned / always_read：`is_pinned=true` 或 `read_policy=always`，每次 prompt 必读，不参与 topK。
- 普通 active：`status=active`、`read_policy=relevant`、未过期，只按 topK 进入 prompt。
- 短期记忆：通过 `expires_at` 控制，过期后不进入 prompt。

`archived`、`superseded`、`deleted`、`read_policy=never` 和已过期记忆不会进入 prompt。未来管理界面应允许用户手动设置 pinned 与可遗忘记忆。

## GPT-SoVITS

`neutral` 是默认语音参考。没有明确选择 emotion 时使用 `neutral`。明确选择其他 emotion 时必须存在对应参考音频，缺失就报错。`prompt_text` 可以为空。
