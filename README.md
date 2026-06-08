# 虚拟人物陪伴系统

## 项目简介

这是一个本地运行的虚拟人物陪伴系统。用户可以选择不同虚拟人物进行对话，并通过人设编辑工作台持续调整人物表达。系统目标不是做一个简单问答机器人，而是让同一个角色在不同场景中延续对用户的理解。

当前重点是角色聊天、人物包管理、人设反馈和本地单用户使用体验。后续预留日程管理、日记阅读和共享关系记忆等场景，但这些业务目前尚未完整实现。

## 主要功能

- 本地单用户登录锁。
- 角色聊天，聊天记录保存到 PostgreSQL。
- 多人物角色包管理。
- 角色头像上传。
- 人设编辑工作台。
- 逐条评价角色回复是否符合人设。
- 发送给人设编辑 AI 进行多轮讨论。
- AI 生成最终人设修改方案和 `preview_character_json`。
- 用户确认后才写入 `character.json`。
- 上一版人设备份与回滚。
- PostgreSQL 保存聊天、记忆、知识库、反馈和本地用户数据。
- Docker Compose 启动 PostgreSQL 和 Adminer。
- 可选 GPT-SoVITS 语音接口。
- 未来预留：日程管理、日记系统、共享关系记忆。

## 最新项目结构

```text
chatbot/
  backend/
    main.py
    api/                         旧 API 兼容层逐步清理中
    core/                        配置、通用 schema、安全工具
    modules/
      auth/
      chat/
      characters/
        api.py
        service.py
        repository.py
        schemas.py
        pack_loader.py
        pack_writer.py
        validator.py
        templates/
          default_character.json
        packs/
          role01/
            character.json
            voice_refs/
              neutral/
                .gitkeep
            backups/
              .gitkeep
          .trash/
            .gitkeep
      persona_review/
      memory/
      knowledge/
      voice/
      relationship_memory/
      schedule/
      diary/
      debug/
    database/
      migrations/
    services/                    非人物系统的旧服务逐步迁移中
    tools/
      character_pack.py
    outputs/
    requirements.txt
  frontend/
    simple_web/
  docker-compose.yml
  run_app.bat
  run_app.ps1
  暂时暂停Chatbot.bat
  彻底停止Chatbot.bat
```

人物系统统一在 `backend/modules/characters`。

公共模板在：

```text
backend/modules/characters/templates/
```

每个角色一个目录：

```text
backend/modules/characters/packs/{character_id}/
```

角色数据唯一来源是：

```text
backend/modules/characters/packs/{character_id}/character.json
```

旧目录 `backend/data/character_packs` 已废弃并删除。不要再把新角色放回旧目录。

`schedule` 和 `diary` 目前只是预留模块，尚未实现完整业务。

## 环境准备

需要：

- Windows
- Docker Desktop
- Conda 环境 `3-chatbot`
- Python 依赖来自 `backend/requirements.txt`
- 本地 `backend/.env`
- 可选 GPT-SoVITS API

## 后端 .env

首次运行前可以复制示例：

```powershell
copy .env.example backend\.env
```

`backend/.env` 至少需要关注：

```text
DATABASE_URL="postgresql://chatbot:change_me_local_only@127.0.0.1:5432/role_chatbot"
LLM_PROVIDER="openai"
OPENAI_API_KEY="your_api_key_here"
OPENAI_BASE_URL="https://your-openai-compatible-base-url.example.com"
OPENAI_MODEL="your_model_name_here"
JWT_SECRET_KEY="change_this_to_a_long_random_string"
JWT_EXPIRE_MINUTES="10080"
UPLOAD_DIR="./data/uploads"
AVATAR_MAX_SIZE_MB="5"
GPTSOVITS_BASE_URL="http://127.0.0.1:9880"
```

不要提交真实 API Key、数据库密码、JWT 密钥或本地私有配置。

## 手动启动

终端 1：

```powershell
cd E:\my_software\chatbot
docker compose up -d
```

终端 2：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

浏览器访问：

```text
http://127.0.0.1:8000/app/
```

Adminer：

```text
http://127.0.0.1:8081
```

可选 GPT-SoVITS API 单独启动：

```powershell
cd E:\GPT-SoVITS\GPT-SoVITS-v2pro-20250604
runtime\python.exe -I api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS\configs\tts_infer.yaml
```

GPT-SoVITS 不是默认自动启动项。不开语音时，文字聊天仍可使用。

## 一键启动脚本

入口：

```text
E:\my_software\chatbot\run_app.bat
E:\my_software\chatbot\run_app.ps1
```

说明：

- `run_app.bat` 是双击入口。
- `run_app.bat` 调用同目录的 `run_app.ps1`。
- `run_app.ps1` 使用脚本所在目录作为项目根目录。
- `run_app.ps1` 启动 Docker 数据库、检查 8000 端口、启动后端并打开网页。
- 脚本不会执行 `docker compose down`。
- 脚本不会执行 `docker compose down -v`。
- GPT-SoVITS 默认不自动启动，需要用户按需单独启动。

## 暂时暂停脚本

```text
E:\my_software\chatbot\暂时暂停Chatbot.bat
```

作用：

- 停止监听 8000 的 chatbot 后端进程。
- 停止监听 9880 的 GPT-SoVITS API 进程，如果存在。
- 在项目根目录执行 `docker compose stop`。
- 保留 PostgreSQL 数据和 Docker volume。
- 不执行 `docker compose down -v`。
- 不执行 `wsl --shutdown`。
- 适合中途休息，稍后继续开发。

## 彻底停止脚本

```text
E:\my_software\chatbot\彻底停止Chatbot.bat
```

作用：

- 停止监听 8000 的 chatbot 后端进程。
- 停止监听 9880 的 GPT-SoVITS API 进程，如果存在。
- 在项目根目录执行 `docker compose stop`。
- 执行 `wsl --shutdown`，更彻底释放 Docker/WSL 占用内存。
- 保留 PostgreSQL volume。
- 不执行 `docker compose down -v`。

注意：`wsl --shutdown` 会关闭所有 WSL，包括 Docker Desktop 后端和其他 WSL 终端。

## 数据保护

不要随便执行：

```powershell
docker compose down -v
```

这会删除 PostgreSQL volume，导致以下数据全部丢失：

- 聊天记录
- 记忆
- 知识库
- 本地用户
- 人设反馈

普通暂停或释放内存时，请使用：

```powershell
docker compose stop
```

## 数据库备份与恢复

备份：

```powershell
cd E:\my_software\chatbot
docker exec -t role-chatbot-postgres pg_dump -U chatbot -d role_chatbot > backup_role_chatbot.sql
```

恢复：

```powershell
Get-Content .\backup_role_chatbot.sql | docker exec -i role-chatbot-postgres psql -U chatbot -d role_chatbot
```

## 人物管理

新增角色：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m tools.character_pack new asa_mitaka --name "三鹰朝"
```

校验角色：

```powershell
python -m tools.character_pack validate asa_mitaka
```

删除角色：

```powershell
python -m tools.character_pack delete asa_mitaka
```

恢复角色：

```powershell
python -m tools.character_pack restore asa_mitaka
```

列出角色：

```powershell
python -m tools.character_pack list
```

删除只是移动到：

```text
backend/modules/characters/packs/.trash/
```

不会删除历史聊天。

Debug：

```text
GET /debug/characters
GET /debug/characters/{character_id}
```

## 人设编辑工作台

流程：

1. 在聊天记录中选择一条或多条角色回复。
2. 输入对回复的人设评价。
3. 可点击标签把常用评价插入输入框。
4. 发送给人设编辑 AI。
5. 多轮讨论修改方向。
6. 生成最终修改方案和 `preview_character_json`。
7. 用户确认后应用修改，才写入 `character.json`。
8. 不满意时可以回滚到上一版。

相关接口：

```text
POST /characters/{character_id}/persona-review/chat
POST /characters/{character_id}/persona-review/finalize
POST /characters/{character_id}/persona-review/apply
POST /characters/{character_id}/persona-review/rollback
```

人设编辑通过 `backend/modules/characters` 读写角色包。备份路径：

```text
backend/modules/characters/packs/{character_id}/backups/character.previous.json
```

## 注意事项

- 不要提交 `backend/.env`、根目录 `.env` 或任何 `.env.*` 本地配置。
- 不要提交真实 API Key、数据库密码、Token、JWT 密钥或私钥文件。
- 不要提交官方头像、语音、模型权重或其他本地素材。
- `character.json` 可以提交。
- `voice_refs` 下的音频、`backups` 和 `.trash` 默认被忽略。
