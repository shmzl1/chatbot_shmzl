# Codex 协作指南

本项目当前原则是只保留最新机制，错误必须暴露。

## 不要恢复

- 不要恢复旧 `OPENAI_*` 配置读取。
- 不要恢复 `LLM_PROVIDER`。
- 不要恢复 `auto`、`mock` 或 `fallback`。
- 不要在模型失败后生成模拟回复。
- 不要在 JSON 非法时自动截取、修补或重试成成功。
- 不要让角色、聊天、语音、人设编辑运行路径依赖旧 wrapper。

## LLM

普通聊天只走 `CHAT_*`。人设编辑只走 `PERSONA_EDITOR_*`。两个 provider 都只能是 `openai`。

缺配置、模型失败、超时、JSON 解析失败都应直接报错，并说明 profile、model 和具体错误；错误信息不能包含 API Key。

## 人设编辑

`finalize` 使用 patch 模式：模型只输出 patch JSON，后端合并 patch，生成 `preview_character_json`，校验通过后返回。`apply` 仍然必须由用户确认后才写入。

patch 不能修改 `id`、`display_name`、`avatar_url`、`voice`、`gptsovits_base_url`、`ref_audio_path`、`prompt_text`。

## 语音

`neutral` 是默认语音参考。GPT-SoVITS 的 `prompt_text` 可以为空。用户明确选择非 neutral emotion 时，缺少该 emotion 的参考音频必须直接报错。
