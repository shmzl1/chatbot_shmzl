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
    main.py
    modules/
      characters/
        packs/
          .trash/
          {character_id}/
            character.json
            voice_refs/
            backups/
    outputs/
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
APP_DATA_DIR="./data"
SQLITE_DB_PATH="./data/chatbot.db"
UPLOAD_DIR="./data/uploads"
BACKUP_DIR="./data/backups"
```

后端启动时会自动创建 `backend/data/`、`backend/data/chatbot.db`、`backend/data/uploads/` 和 `backend/data/backups/`，并执行 `backend/database/sqlite_migrations/` 中尚未执行的迁移。前端不直接读写数据库，只通过 FastAPI 访问数据。

运行数据的位置如下：

- `backend/data/chatbot.db`：聊天、日记、日程、记忆、知识库、反馈和用户数据。
- `backend/modules/characters/packs/{character_id}/character.json`：正式角色包；每个角色使用独立目录。
- `backend/data/uploads/diary/images/`：日记图片。
- `backend/data/uploads/avatars/user/` 和 `backend/data/uploads/avatars/characters/`：用户与角色头像。
- `backend/data/backups/`：后端启动时创建的本地备份目录。
- `backend/outputs/`：由后端通过 `/outputs` 提供的本地输出文件。

这些目录可能包含私人聊天、日记和媒体数据。不要提交真实 `.env`、私人数据库或附件，也不要提交未经授权的素材、语音文件和模型权重。

## 环境变量

在仓库根目录复制环境变量示例：

```powershell
Copy-Item backend\.env.example backend\.env
```

普通聊天和人设编辑使用相互独立的 LLM 配置：前者使用 `CHAT_*`，后者使用 `PERSONA_EDITOR_*`。不要提交真实 API Key，不要提交 `backend/.env`。

其他关键配置包括：

- `DEFAULT_CHARACTER_ID`：正式默认角色 ID，默认值为 `role01`。
- `APP_DATA_DIR`、`SQLITE_DB_PATH`、`UPLOAD_DIR`、`BACKUP_DIR`、`OUTPUTS_DIR`：本地数据路径。
- `GPTSOVITS_BASE_URL`、`GPTSOVITS_TIMEOUT_SECONDS`：可选语音服务。
- `TOP_K_*`、`STYLE_SCORE_THRESHOLD`：记忆和角色素材检索参数。

项目不保留旧 `OPENAI_*`、`LLM_PROVIDER`、`auto`、`mock` 或 `fallback` 路径。缺配置、模型失败、JSON 非法都会直接报错。

## 后端启动

在已激活的 Python 环境中，从仓库根目录安装依赖：

```powershell
Set-Location backend
python -m pip install -r requirements.txt
```

从仓库根目录启动后端：

```powershell
Set-Location backend
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

`frontend/desktop/` 是唯一前端，使用 Electron、React、TypeScript、Vite、Tailwind CSS、Radix UI、TanStack Query、Zustand 和 react-markdown。

从仓库根目录运行：

```powershell
Set-Location frontend\desktop
npm install
npm run desktop
```

开发模式：

```powershell
npm run dev
```

桌面端默认连接 `http://127.0.0.1:8000`。如果后端使用其他端口，可以在设置页修改后端地址；该地址保存在 localStorage。前端不使用 token 或 Bearer 登录态，也不直接读取 SQLite 文件，只调用 FastAPI。

## 一键启动脚本

```powershell
.\scripts\runtime\run_app.ps1
```

或双击：

```text
scripts/runtime/run_app.bat
```

脚本使用名为 `3-chatbot` 的 Conda 环境，只检查 Conda 和后端依赖，然后启动 FastAPI 并打开接口文档；桌面端仍按上节命令启动。脚本不会检查 Docker，也不会启动数据库容器。

## 当前主要功能

- 聊天：多会话、新建、搜索、重命名、归档和恢复；历史会话按自身角色继续对话。
- 日记：CRUD、搜索和筛选、心情与标签、图片附件，以及用户主动选择后的“让角色读这篇日记”。
- 日程：任务 CRUD、今日任务、月历、筛选、完成、跳过和延期。
- 设置：本地用户资料与头像、后端地址、连接状态和第三方开源声明。
- 角色与人设：角色选择、角色包管理、头像、校验，以及经过预览和用户确认的人设修正。
- 底层能力：长期记忆、关系记忆、知识库，以及可选 GPT-SoVITS 语音。

日记和日程默认都不会自动进入聊天 prompt。只有用户点击“让角色读这篇日记”时，所选日记才会作为新对话的上下文。

GPT-SoVITS 是可选服务，不会随应用自动启动。未指定情绪时使用 `neutral`；明确指定其他情绪时必须存在对应参考音频，缺失时会直接报错，不会静默回退到 `neutral`。

## 本地用户

项目是本地单用户模式，不需要注册、登录、密码或 JWT。后端会创建或复用唯一的本地用户；数据库中存在多个用户时会明确报错，避免旧数据关联错乱。设置页可以修改显示 ID、用户名和本地头像。

## 默认角色

正式角色只从 `backend/modules/characters/packs/{character_id}/character.json` 加载。`role01` 是系统正式默认角色，不是 mock；它的正式文件是 `backend/modules/characters/packs/role01/character.json`。后端默认配置为 `DEFAULT_CHARACTER_ID=role01`，前端统一使用同一默认 ID。首次启动或没有保存过角色时，只有在角色列表中确实存在 `role01` 才会选择它；用户保存的其他有效角色会继续优先使用；保存角色失效时恢复到 `role01`。如果 `role01` 缺失，前端显示默认角色配置缺失并禁止角色相关操作，不会改用角色列表第一项。

## 正式接口概览

正式路由由 `backend/modules/*` 注册，后端不注册以 `/debug` 为前缀的路由组。完整请求字段、响应字段和状态码以启动后的 `/docs` 为准。

| 功能 | 正式路径 |
| --- | --- |
| 健康检查和接口文档 | `/health`、`/docs` |
| 本地用户 | `/auth/status`、`/auth/me`、`/auth/me/avatar`、`/auth/logout` |
| 角色 | `/characters`、`/characters/{character_id}`、`/characters/{character_id}/*` |
| 聊天和会话 | `/chat`、`/chat/text`、`/chat/sessions*` |
| 日记和图片 | `/diary/entries*`、`/diary/images*` |
| 日程 | `/schedule/items*`、`/schedule/today`、`/schedule/calendar`、`/schedule/occurrences*` |
| 人设反馈与修正 | `/feedback/persona/*`、`/characters/{character_id}/persona-review/*` |
| 长期记忆 | `/memory*` |
| 关系记忆 | `/relationship-memory*`，其中 `/relationship-memory/debug` 是该模块的正式审计接口 |
| 知识库 | `/knowledge*` |
| 可选语音 | `/voice/test` |
| 本地静态文件 | `/uploads/*`、`/outputs/*` |

## 更多文档

- [架构说明](docs/ARCHITECTURE.md)
- [第三方开源声明](THIRD_PARTY_NOTICES.md)
