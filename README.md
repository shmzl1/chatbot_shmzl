# 虚拟人物陪伴系统

## 项目简介

这是一个本地运行的虚拟人物陪伴系统。

项目重点不是做普通问答机器人，而是围绕“人物”建立长期对话体验：
用户可以选择不同虚拟人物聊天，也可以通过人设编辑工作台持续修正人物表达。

当前版本以本地单用户使用为主，默认角色是 `role01`。
系统已经把人物相关能力集中到 `backend/modules/characters` 模块。

## 当前功能

- 本地单用户登录保护。
- 角色聊天和聊天记录保存。
- 多人物角色包读取、创建、更新、删除、恢复。
- 角色头像上传。
- 人设编辑工作台。
- 对角色回复进行逐条评价。
- 与人设编辑 AI 多轮讨论修改方向。
- 生成最终人设修改方案和 `preview_character_json`。
- 用户确认后才写入角色 `character.json`。
- 人设修改前自动备份上一版。
- 支持上一版人设回滚。
- PostgreSQL 保存聊天、记忆、知识库、反馈等数据。
- Docker Compose 提供 PostgreSQL 和 Adminer。
- 可选接入 GPT-SoVITS 语音服务。

日程、日记和更完整的共享关系记忆仍属于后续规划。

## 最新结构

```text
chatbot/
  backend/
    main.py
    core/                         通用配置、schema、安全工具
    api/                          旧 API 兼容层和少量入口
    modules/
      auth/                       登录模块
      chat/                       普通聊天模块
      characters/                 人物系统核心模块
      persona_review/             人设编辑模块
      memory/                     记忆模块
      knowledge/                  知识库模块
      voice/                      语音模块
      relationship_memory/        共享关系记忆预留模块
      schedule/                   日程预留模块
      diary/                      日记预留模块
      debug/                      调试接口模块
    services/                     仍在逐步迁移的旧服务
    database/                     数据库和迁移脚本
    tools/
      character_pack.py           人物包 CLI
    outputs/                      本地输出目录
  frontend/
    simple_web/                   当前简单网页前端
  docs/                           架构和 Codex 协作文档
  docker-compose.yml
  run_app.bat
  run_app.ps1
  暂时暂停Chatbot.bat
  彻底停止Chatbot.bat
  计划书.md
```

## 人物系统路径

人物系统现在集中在：

```text
backend/modules/characters/
```

公共模板在：

```text
backend/modules/characters/templates/
```

每个角色一个独立目录：

```text
backend/modules/characters/packs/{character_id}/
```

默认角色已经迁移到：

```text
backend/modules/characters/packs/role01/
```

每个角色包里，唯一必需文件是 `character.json`。
角色语音参考素材放在本角色目录的 `voice_refs/`。
人设上一版备份放在本角色目录的 `backups/`。

旧目录 `backend/data/character_packs` 已废弃。
新增角色不要再放到旧目录，也不要让新代码恢复旧路径依赖。

## 启动方式

首次使用前，建议创建后端环境并安装依赖：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
pip install -r requirements.txt
```

启动数据库：

```powershell
cd E:\my_software\chatbot
docker compose up -d postgres adminer
```

启动后端：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

前端是 `frontend/simple_web` 下的简单网页。
也可以使用项目根目录的 `run_app.bat` 或 `run_app.ps1` 辅助启动。

## 一键启动和暂停脚本

推荐双击项目根目录的 `run_app.bat` 启动系统。

脚本分工：

- `run_app.bat` 是 Windows 双击入口。
- `run_app.ps1` 是实际启动逻辑。
- `暂时暂停Chatbot.bat` 用于临时暂停本地服务。
- `彻底停止Chatbot.bat` 用于更彻底释放 WSL 和 Docker 占用的内存。

`run_app.bat` 会切换到脚本所在目录，
然后用 `-ExecutionPolicy Bypass` 调用同目录的 `run_app.ps1`。

`run_app.ps1` 会：

- 启动 `postgres` 和 `adminer` 容器。
- 等待 `role-chatbot-postgres` 变为 healthy。
- 检查 `conda` 和 `3-chatbot` 环境。
- 检查后端基础依赖。
- 如果 8000 端口已被占用，只提示并打开已有页面。
- 打开 `http://127.0.0.1:8000/app/`。
- 使用 `conda run` 启动 FastAPI 后端。

GPT-SoVITS 不会由启动脚本自动启动。
如需语音功能，请单独启动 9880 API。

`暂时暂停Chatbot.bat` 会停止：

- 监听 8000 的后端进程。
- 监听 9880 的 GPT-SoVITS API 进程。
- Docker Compose 当前项目容器。

它只执行 `docker compose stop`，会保留数据库 volume 和聊天数据。

`彻底停止Chatbot.bat` 会在上述暂停动作之外执行：

```powershell
wsl --shutdown
```

这会关闭所有 WSL，包括 Docker Desktop 后端和其他 WSL 终端，
适合需要更彻底释放内存时使用。

所有启动/暂停脚本都使用 UTF-8 编码，并保持正常多行换行。
所有脚本都不能执行 `docker compose down -v`。

## LLM 模型配置

普通聊天和人设编辑现在使用两套模型配置。

普通聊天使用 `CHAT_*` 配置：

```env
CHAT_LLM_PROVIDER="openai"
CHAT_OPENAI_API_KEY=""
CHAT_OPENAI_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
CHAT_OPENAI_MODEL="doubao-seed-character-251128"
CHAT_OPENAI_TIMEOUT_SECONDS="120"
CHAT_OPENAI_TEMPERATURE="0.8"
```

人设编辑使用 `PERSONA_EDITOR_*` 配置：

```env
PERSONA_EDITOR_LLM_PROVIDER="openai"
PERSONA_EDITOR_OPENAI_API_KEY=""
PERSONA_EDITOR_OPENAI_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
PERSONA_EDITOR_OPENAI_MODEL="doubao-seed-2-0-pro-260215"
PERSONA_EDITOR_OPENAI_TIMEOUT_SECONDS="180"
PERSONA_EDITOR_OPENAI_TEMPERATURE="0.2"
```

这样可以让普通聊天模型更偏角色表达和人设还原，
让人设编辑模型更偏分析、稳定输出 JSON 和生成修改方案。

两套配置可以使用同一个 API Key，也可以指向不同模型。

项目不保留旧 `OPENAI_*` 兼容机制。
普通聊天不会读取人设编辑模型配置。
人设编辑也不会读取普通聊天模型配置。

如果 `CHAT_*` 或 `PERSONA_EDITOR_*` 缺少必需项，接口会直接报错。

项目不使用 `LLM_PROVIDER=auto`。
项目不允许 `mock` provider。

## 无静默兜底策略

本项目不在关键错误后生成模拟结果。

- LLM 配置错误会直接报错。
- LLM 请求失败会直接报错。
- LLM 返回 JSON 解析失败会直接报错。
- 角色 JSON 错误会直接报错。
- 人设编辑 JSON 解析失败会直接报错。
- GPT-SoVITS 语音失败会直接报错。
- 项目不会在模型失败时返回模拟角色回复。

这样做是为了本地调试时尽快暴露真实问题。

## 人物包 CLI

进入后端目录：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
```

列出角色：

```powershell
python -m tools.character_pack list
```

创建角色：

```powershell
python -m tools.character_pack new asa_mitaka --name "三鹰朝"
```

校验角色：

```powershell
python -m tools.character_pack validate asa_mitaka
```

安全删除角色：

```powershell
python -m tools.character_pack delete asa_mitaka
```

恢复角色：

```powershell
python -m tools.character_pack restore asa_mitaka
```

删除角色只是移动到 `.trash`，不会删除历史聊天记录。

## 调试接口

人物系统提供以下调试接口：

```text
GET /debug/characters
GET /debug/characters/{character_id}
```

人设编辑接口仍保持原有路径：

```text
POST /characters/{character_id}/persona-review/chat
POST /characters/{character_id}/persona-review/finalize
POST /characters/{character_id}/persona-review/apply
POST /characters/{character_id}/persona-review/rollback
```

## 数据保护

- 不要提交 `.env`。
- 不要提交数据库文件和本地输出。
- 不要提交官方头像、语音素材、模型权重。
- 不要把真实私人聊天记录提交到 Git。
- 不要永久删除角色包，优先使用 `.trash` 安全删除。
- 人设编辑只有 `apply` 会写入 `character.json`。
- `chat` 和 `finalize` 只生成讨论内容或预览方案。

## 文档编码和 AI 读取说明

本项目 Markdown 文档统一使用 UTF-8 编码。

如果 Codex、IDE、脚本或其他 AI 工具读取文档时出现乱码、截断或结构混乱，
请优先检查以下问题：

- 文件是否按 UTF-8 保存。
- 终端是否按 UTF-8 显示中文。
- Markdown 标题是否单独成行。
- 段落之间是否有空行。
- 列表项是否逐行书写。
- 是否存在过长单行文本。

新增文档时请保持普通 Markdown 格式，不要把大段内容压成一行。

## 更多文档

- [项目计划书](计划书.md)
- [架构说明](docs/ARCHITECTURE.md)
- [Codex 协作指南](docs/CODEX_GUIDE.md)
- [模块说明](backend/modules/README.md)
