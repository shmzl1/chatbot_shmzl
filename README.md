# Local Role Voice Chatbot

## 项目简介

这是一个本地角色聊天机器人项目，用于调试角色卡、长期记忆、知识库检索、OpenAI 兼容模型接入和网页端聊天体验。当前版本以本地开发为主，后端提供 FastAPI 接口，前端提供浏览器调试界面，数据库使用 PostgreSQL 保存会话、反馈、知识库和长期记忆。

## 技术栈

- 后端：Python、FastAPI、Uvicorn、Pydantic
- 数据库：PostgreSQL、psycopg
- 前端：HTML、CSS、原生 JavaScript
- 本地服务：Docker Compose、Adminer
- AI 接入：OpenAI 兼容 Chat Completions API，可用于火山引擎 Ark 等兼容服务

## 目录结构

```text
chatbot/
├─ backend/                 后端服务
│  ├─ core/                 配置与数据结构
│  ├─ services/             LLM、数据库、记忆、知识库等服务
│  ├─ scripts/              数据导入、导出和评估脚本
│  ├─ data/                 示例角色、知识库和本地资料
│  ├─ requirements.txt      后端依赖
│  └─ .env.example          后端环境变量示例
├─ frontend/
│  └─ simple_web/           浏览器前端
├─ docker-compose.yml       PostgreSQL 和 Adminer
├─ run_app.bat              Windows 一键启动脚本
├─ run_app.ps1              PowerShell 一键启动脚本
├─ .env.example             根目录环境变量示例
├─ .gitignore               Git 忽略规则
└─ README.md                项目说明
```

## 安装后端依赖

你可以先手动进入自己的 Conda 环境，再安装依赖：

```powershell
conda activate 3-chatbot
cd backend
python -m pip install -r requirements.txt
```

## 环境变量配置

不要把真实 API Key 写进仓库。首次运行前，把示例配置复制为本地配置：

```powershell
copy .env.example backend\.env
```

然后编辑 `backend/.env`，填写自己的数据库地址、模型地址、模型名称和 API Key。

常用变量：

```text
DATABASE_URL="postgresql://your_db_user:your_db_password@127.0.0.1:5432/your_db_name"
LLM_PROVIDER="auto"
OPENAI_API_KEY="your_api_key_here"
OPENAI_BASE_URL="https://your-openai-compatible-base-url.example.com/api/v3"
OPENAI_MODEL="your_model_name_here"
```

说明：

- `LLM_PROVIDER="auto"` 表示有模型配置时调用真实 API，没有配置时走本地候选回复。
- `OPENAI_BASE_URL` 填基础地址，不要带 `/chat/completions`。
- 如果你用 Docker Compose 自定义 PostgreSQL 账号密码，也可以把 `.env.example` 复制成根目录 `.env`，再改 `POSTGRES_DB`、`POSTGRES_USER`、`POSTGRES_PASSWORD`。

## 启动方式

推荐使用根目录的一键脚本：

```powershell
.\run_app.ps1
```

或双击：

```text
run_app.bat
```

脚本会尝试使用 `3-chatbot` Conda 环境，并启动本地后端。启动后在浏览器打开：

```text
http://127.0.0.1:8000/app/
```

如果不用一键脚本，也可以手动启动：

```powershell
conda activate 3-chatbot
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

数据库管理页面：

```text
http://127.0.0.1:8081
```

Adminer 登录信息请以你本地 `.env` 或 `docker-compose.yml` 中的 PostgreSQL 配置为准。

## 注意事项

- 不要提交 `backend/.env`、根目录 `.env` 或任何 `.env.*` 本地配置文件。
- 不要把 OpenAI API Key、火山引擎 Ark API Key、数据库密码、Token、私钥文件提交到 GitHub。
- 上传前请检查截图、日志、数据库导出、语音素材和临时文件，它们可能包含私人信息。
