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

## 语音

普通聊天没有显式 emotion 选择时，语音合成使用默认 `neutral` 参考音频。
