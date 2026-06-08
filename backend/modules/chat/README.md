# chat 模块

`chat` 模块负责普通角色聊天。

## 职责

- 接收前端聊天请求。
- 读取当前角色信息。
- 调用检索、记忆和 LLM 相关服务。
- 保存聊天会话和聊天轮次。
- 返回角色文本回复和可选语音信息。

## LLM profile

普通聊天使用 `chat` profile。

配置项为：

- `CHAT_LLM_PROVIDER`
- `CHAT_OPENAI_API_KEY`
- `CHAT_OPENAI_BASE_URL`
- `CHAT_OPENAI_MODEL`
- `CHAT_OPENAI_TIMEOUT_SECONDS`
- `CHAT_OPENAI_TEMPERATURE`

如果这些配置未填写，系统会兼容读取旧 `OPENAI_*` 配置。
如果最终有效配置仍缺失，聊天接口会直接报错。

## 人物依赖

聊天所需的人物数据应通过 `modules.characters` 获取。

不要在本模块中拼接角色包路径。
不要读取旧的 `backend/data/character_packs`。

## 边界

本模块不负责人设修改。

如果用户要修正角色设定，应走 `persona_review` 流程。

## 注意事项

- 不要改变普通聊天接口路径。
- 不要静默吞掉角色包读取错误。
- 不要在 LLM 失败后返回模拟角色回复。
- 不要因为语音失败破坏文字聊天返回。
