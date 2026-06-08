# 后端模块说明

`backend/modules` 是后端业务模块目录。

每个子目录代表一个相对独立的业务能力。
新增功能应优先放入对应模块，而不是继续扩大旧的 `backend/services`。

## 当前模块

- `auth`：本地登录和认证保护。
- `chat`：普通聊天入口。
- `characters`：人物系统和角色包管理。
- `persona_review`：人设编辑工作台后端。
- `memory`：长期记忆。
- `knowledge`：知识库。
- `voice`：语音调用。
- `debug`：调试接口。
- `health`：健康检查。
- `relationship_memory`：共享关系记忆预留。
- `schedule`：日程预留。
- `diary`：日记预留。

## 模块约定

模块内通常可以包含：

- `api.py`：FastAPI router。
- `service.py`：业务逻辑。
- `schemas.py`：本模块请求和响应模型。
- `README.md`：模块说明。

如果模块涉及文件系统边界，可以继续拆出 repository、loader、writer、validator。

## 人物系统

人物系统集中在：

```text
backend/modules/characters/
```

角色包集中在：

```text
backend/modules/characters/packs/
```

其他模块需要角色数据时，应通过 `characters` 模块读取。

## 文档编码

本目录下 Markdown 文档统一使用 UTF-8。

如果 AI 工具读取异常，先检查编码、换行和过长单行。
