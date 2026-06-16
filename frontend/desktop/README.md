# 桌面端前端

`frontend/desktop` 是本项目唯一前端。旧 `frontend/simple_web` 已删除，不再通过 `/app/` 使用主界面。

## 技术栈

- Electron
- React
- TypeScript
- Vite
- Tailwind CSS
- Radix UI
- TipTap
- react-markdown
- Zustand
- TanStack Query
- lucide-react

## 后端地址

默认连接：

```text
http://127.0.0.1:8000
```

如果后端改用其他端口，可在设置页改成：

```text
http://127.0.0.1:8010
http://127.0.0.1:18000
```

地址会保存到 localStorage。前端不使用 token、Bearer 或登录态。

## 启动

安装依赖：

```powershell
cd E:\my_software\chatbot\frontend\desktop
npm install
```

浏览器开发模式：

```powershell
npm run dev
```

Electron 桌面端：

```powershell
npm run desktop
```

构建检查：

```powershell
npm run build
```

后端需要用户手动启动：

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

后端默认使用本地 SQLite 文件：

```text
E:\my_software\chatbot\backend\data\chatbot.db
```

普通启动不需要 Docker、PostgreSQL 或 Adminer。前端不直接读写数据库文件，只通过 FastAPI 调用接口。

端口 8000 被占用时：

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8010
```

## 页面

- 聊天：发送普通聊天；选中日记时发送 `diary_entry_id`。
- 日记：列表、搜索、日期筛选、新建、编辑、保存、删除、心情、标签、图片上传、缩略图、删除图片、让角色读这篇日记。
- 日程：任务 CRUD、选中日期任务、月历汇总、类型和状态筛选、完成、延期、跳过、标签、优先级和预计用时，全部通过 FastAPI 读写本地 SQLite。
- 设置：默认用户头像、显示 ID / 用户名、后端地址、连接状态、角色和记忆高级入口说明、第三方开源声明入口。
