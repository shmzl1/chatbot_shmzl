# 架构说明

后端运行入口是 `backend/main.py`，路由注册来自 `backend/modules/*`。角色相关能力的唯一入口是 `backend/modules/characters`。

## 数据流

普通聊天：

```text
frontend
  -> modules.chat.api
  -> modules.characters.service
  -> retrieval / memory / chat LLM profile
  -> database
```

人设编辑：

```text
frontend
  -> characters persona-review endpoints
  -> modules.persona_review.service
  -> persona_editor LLM profile
  -> patch
  -> preview_character_json
  -> user confirmed apply
  -> modules.characters validation and write
```

语音：

```text
frontend
  -> modules.voice.api or chat voice option
  -> services.tts_service
  -> GPT-SoVITS /tts
```

## LLM

普通聊天只读取 `CHAT_*`，人设编辑只读取 `PERSONA_EDITOR_*`。两个 profile 都只允许 provider 为 `openai`。

项目不读取旧 `OPENAI_*` 配置，不读取 `LLM_PROVIDER`，不允许 `auto`、`mock` 或 `fallback`。缺配置、模型失败、超时和 JSON 非法都会直接暴露为错误。

## JSON

LLM JSON 使用严格 `json.loads`。后端不会从 Markdown 代码块或自然语言中截取 JSON，也不会自动修补非法 JSON。

## GPT-SoVITS

`neutral` 是默认语音参考。没有明确选择 emotion 时使用 `neutral`。明确选择其他 emotion 时必须存在对应参考音频，缺失就报错。`prompt_text` 可以为空。
