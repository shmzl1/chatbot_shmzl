# Codex 协作指南

本项目当前原则是只保留最新机制，错误必须暴露。

## 中文 Markdown 编码规则

中文 Markdown 文档必须按 UTF-8 读取和写入，包括根目录文档、`docs/` 下的说明文档和中文命名的 `.md` 文件。

在 PowerShell 中读取中文 Markdown 时，禁止使用 `type`、`cat` 或不带编码参数的默认 `Get-Content`。这些命令可能受终端代码页或 PowerShell 默认编码影响，导致中文显示为乱码、`�` 或问号。

推荐使用：

```powershell
Get-Content -Raw -Encoding UTF8 docs/CODEX_GUIDE.md
```

也可以使用 Python 显式指定 UTF-8：

```python
from pathlib import Path

text = Path("docs/CODEX_GUIDE.md").read_text(encoding="utf-8")
```

写入中文 Markdown 时也必须显式使用 UTF-8。不要因为终端显示异常就判断文件已经损坏；应先用 UTF-8 方式重新读取，并检查编辑器编码和终端编码。

如果读取结果中出现乱码、`�` 或异常问号，必须立即停止修改当前文档，重新按 UTF-8 读取原文件。不能根据乱码内容猜测、补写或改写文档，也不能把乱码保存回文件。

## 文件位置

- 唯一 env 示例：`backend/.env.example`。
- 用户本地真实配置：`backend/.env`。
- 不要恢复根目录 `.env.example`。
- Docker Compose 文件：`deploy/docker/docker-compose.yml`。
- 启动/暂停脚本目录：`scripts/runtime/`。
- 计划书唯一位置：`docs/计划书.md`。
- Python 后端依赖文件唯一位置：`backend/requirements.txt`。
- 关系记忆模块位置：`backend/modules/relationship_memory/`。
- 唯一前端位置：`frontend/desktop/`。
- 不要恢复根目录 `requirements.txt`，不要把 `backend/requirements.txt` 复制到根目录。
- 不要恢复 `frontend/simple_web`，不要恢复旧 HTML + app.js 前端，不要恢复 `/app/` 静态主界面。

从项目根目录安装后端依赖时使用：

```powershell
cd E:\my_software\chatbot
conda activate 3-chatbot
python -m pip install -r backend\requirements.txt
```

从后端目录安装后端依赖时使用：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m pip install -r requirements.txt
```

Docker Compose 命令必须使用：

```powershell
docker compose --project-directory . -f deploy/docker/docker-compose.yml ...
```

## 桌面端前端

项目现在只有 Electron 桌面端前端，位于 `frontend/desktop/`。技术栈是 Electron + React + TypeScript + Vite + Tailwind CSS + Radix UI + TipTap + react-markdown + Zustand + TanStack Query + lucide-react。

后端仍是 FastAPI，默认地址 `http://127.0.0.1:8000`。桌面端设置页可以把后端地址改为 `http://127.0.0.1:8010` 或 `http://127.0.0.1:18000`。前端不使用 token、Bearer 或登录态。

后端不再挂载 `/app/`。用户查看接口文档使用 `http://127.0.0.1:8000/docs`，主界面通过 Electron 桌面端启动。

## 默认不要自动执行

除非用户明确要求，不要自动执行：

- `uvicorn main:app --reload`
- `docker compose up`
- `docker compose down`
- `docker compose down -v`
- `git commit`
- `git push`

文档里可以告诉用户手动执行正确命令，但 Codex 不要代替用户启动服务、删除容器或提交代码。

## 不要恢复

- 不要恢复旧 `OPENAI_*` 配置读取。
- 不要恢复 `LLM_PROVIDER`。
- 不要恢复 `auto`、`mock` 或 `fallback`。
- 不要在模型失败后生成模拟回复。
- 不要在 JSON 非法时自动截取、修补或重试成成功。
- 不要让角色、聊天、语音、人设编辑运行路径依赖旧 wrapper。

## LLM

普通聊天只走 `CHAT_*`。人设编辑只走 `PERSONA_EDITOR_*`。两个 provider 都只能是 `openai`。

缺配置、模型失败、超时、JSON 解析失败都应直接报错，并说明 profile、model 和具体错误；错误信息不能包含 API Key。

## 本地用户

项目是 Windows 本地单用户模式，不再需要注册、登录、密码、JWT 或 Bearer Token 登录锁。后端会自动确保 `users` 表里有一个默认本地用户；`get_current_user` 只是兼容依赖名，必须直接返回默认用户。

用户可以通过 `/auth/me` 查看和修改显示 ID / 用户名，通过 `/auth/me/avatar` 上传头像。不要修改 `users.id`，不要恢复密码登录、JWT 校验或前端登录页。如果需要清空本地用户数据，应手动清理数据库或另做专门工具。

## 日记

日记模块位于 `backend/modules/diary/`，第一阶段只做本地日记 CRUD、图片附件和用户主动选择后的聊天上下文。不要把日记默认塞进 prompt，不要从日记自动写入长期记忆。

日记图片保存到 `uploads/diary/images/`，数据库只保存附件元数据和 public URL。删除日记或图片采用软删除。

聊天请求只有显式传入 `diary_entry_id` 时，才能通过 `modules.diary.context` 读取该篇日记。普通聊天不应读取全部日记。

## relationship_memory

关系记忆使用 `relationship_memory_events` 表。普通聊天读取有效关系记忆加入长期上下文，同时继续保留 `long_term_memories` 兼容。

用户确认聊天记忆建议后，应同时写入旧 `/memory` 和新 `/relationship-memory`。停用关系记忆只更新 `is_active = false`，不要物理删除事件。

记忆必须分层读取：`is_pinned=true` 或 `read_policy=always` 的 pinned 记忆每次 prompt 必读，不参与 topK；普通记忆只有 `status=active`、`read_policy=relevant` 且未过期时才按 topK 进入 prompt；`archived`、`superseded`、`deleted`、`read_policy=never` 或已过期的记忆不能进入 prompt。AI 不应自动删除或覆盖 pinned 记忆，未来只能由用户在管理界面显式维护。

不要在 relationship_memory 中直接保存日记原文。日记或日程如果要生成长期记忆，必须先成为候选记忆，并经过用户确认。

## 人设编辑

`finalize` 使用 patch 模式：模型只输出 patch JSON，后端合并 patch，生成 `preview_character_json`，校验通过后返回。`apply` 仍然必须由用户确认后才写入。

人设分为固定核心和可变补充。固定核心字段包括 `id`、`display_name`、`core_personality`、`speaking_style`、`relationship_to_user`、`forbidden`、`reply_patterns`、`lore`、`style_contract`，不能被 AI 自动修改、删除、覆盖或压缩，每次聊天 prompt 必须完整读取。`avatar_url` 和 `voice` 是受保护元数据，也不能被人设编辑 AI 自动修改。

可变补充字段包括 `dialogues`、`reactions`、`bad_examples`、`evaluation_criteria`、`revision_notes`。人设编辑 patch 只能追加这些字段对应的补充内容；用户确认 apply 后才允许按上限压缩，裁剪内容必须归档到角色包 `backups/persona_compaction_archive.jsonl`，不能静默丢弃。

## 语音

`neutral` 是默认语音参考。GPT-SoVITS 的 `prompt_text` 可以为空。用户明确选择非 neutral emotion 时，缺少该 emotion 的参考音频必须直接报错。

## UTF-8

Markdown、脚本和 env 示例都应使用 UTF-8。终端中文乱码不等于文件乱码，不要因为终端显示异常就重写中文；先检查终端编码、编辑器编码和文件实际编码。
