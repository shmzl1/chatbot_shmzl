# chat 模块

`chat` 负责普通角色聊天，接口路径保持 `/chat/text` 和 `/chat`。

## LLM

普通聊天只使用 `chat` profile，只读取：

- `CHAT_LLM_PROVIDER`
- `CHAT_OPENAI_API_KEY`
- `CHAT_OPENAI_BASE_URL`
- `CHAT_OPENAI_MODEL`
- `CHAT_OPENAI_TIMEOUT_SECONDS`
- `CHAT_OPENAI_TEMPERATURE`

`CHAT_LLM_PROVIDER` 只能是 `openai`。缺配置、请求失败、超时、JSON 非法都会直接报错。

本模块不读取旧 `OPENAI_*`，不读取 `LLM_PROVIDER`，不允许 `auto`、`mock` 或 `fallback`。风格检查不合格时直接失败，不做本地修复，不生成模拟回复。

## 角色依赖

角色信息只通过 `modules.characters.service` 获取。

## 记忆上下文

普通聊天同时读取旧 `long_term_memories` 和新的 `relationship_memory_events`。关系记忆只读取 `is_active = true` 的事件，并加入 prompt 的“关系长期上下文”。

## 日记上下文

聊天默认不读取日记。请求体只有显式传入 `diary_entry_id` 时，才会通过 `modules.diary.context` 读取当前用户的那一篇日记，并加入 prompt 的“用户主动提供的日记上下文”。日记内容不会自动写入长期记忆。

## 语音

普通聊天没有显式 emotion 选择时，语音合成使用默认 `neutral` 参考音频。
