# 后端模块

`backend/modules` 是后端运行入口目录。新增或修改业务入口时优先放在对应 module 内。

## 当前重点模块

- `characters`：角色系统唯一入口。
- `chat`：普通聊天入口，只使用 `CHAT_*`。
- `persona_review`：人设编辑闭环，只使用 `PERSONA_EDITOR_*`。
- `relationship_memory`：关系长期上下文，保存到 `relationship_memory_events`。
- `voice`：GPT-SoVITS 语音调用。

## 当前原则

- 不读取旧 `OPENAI_*` 配置。
- 不读取 `LLM_PROVIDER`。
- 不允许 `auto`、`mock` 或 `fallback`。
- 缺配置、模型失败、JSON 非法直接报错。
- 角色、聊天、语音、人设编辑运行路径走 module 结构。
