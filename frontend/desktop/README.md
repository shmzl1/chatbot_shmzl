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

服务状态只在异常时出现。连接正常时桌面端不展示常驻状态条；连接失败时显示简短提示，并提供重试和设置入口，提示中不展示 URL、IP 或端口。

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

- 聊天：多会话侧栏、新建对话、搜索、重命名、归档、查看归档和恢复归档。前端使用正式 `/chat/sessions` 接口；从日记页进入聊天时默认开启新对话并携带 `diary_entry_id`。
- 日记：列表、搜索、日期筛选、新建、编辑、保存、删除、心情、标签、图片上传、缩略图、删除图片、让角色读这篇日记。
- 日程：任务 CRUD、选中日期任务、月历汇总、收起式类型和状态筛选、完成、延期、跳过、标签、优先级和预计用时，全部通过 FastAPI 读写本地 SQLite。
- 设置：默认用户头像、显示 ID / 用户名、后端地址、连接状态和第三方开源声明入口。

## 人设修正

聊天页顶部提供“人设修正”入口。入口只在当前会话存在真实角色回复时可用；归档会话也可以打开工作台查看并选择历史片段。工作台使用当前会话绑定的 `character_id`，不会用另一个全局角色误改人设。

流程为：选择最多 5 轮完整“用户消息 + 角色回复”，填写问题标签或具体说明，保存到 `/feedback/persona/turn`，再调用 `/characters/{character_id}/persona-review/chat` 与人设编辑 AI 讨论。生成方案时调用 `finalize`，只展示主要问题、修改计划、风险、patch 摘要和字段差异；用户确认后才调用 `apply`。回滚按钮调用 `rollback`，只恢复最近一次备份。

人设编辑对话不进入普通聊天会话，不写入长期记忆或关系记忆，也不会改写历史聊天消息。

## 当前角色

聊天、日记和日程页面都提供角色选择器。角色列表来自后端 `/characters`，前端只在 localStorage 保存当前角色 ID，不维护硬编码角色列表。

聊天发送必须使用当前选中角色。打开历史会话时，前端会同步该会话的 `character_id`；如果用户在已有会话中切换角色，前端会开启新对话。日记页“让角色读这篇日记”使用当前选中角色，并开启新对话携带该日记上下文。日程数据不按角色隔离，角色选择只作为全局上下文显示。

`role01` 是正式默认角色。没有保存角色时使用 `role01`；保存角色仍存在时继续使用保存角色；保存角色失效时恢复 `role01`；如果角色列表中没有 `role01`，显示默认角色配置缺失并禁止角色相关操作。前端不能使用角色列表第一项作为默认角色。
