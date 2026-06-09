# persona_review 模块

`persona_review` 负责人设编辑闭环。

## LLM

人设编辑只使用 `persona_editor` profile，只读取：

- `PERSONA_EDITOR_LLM_PROVIDER`
- `PERSONA_EDITOR_OPENAI_API_KEY`
- `PERSONA_EDITOR_OPENAI_BASE_URL`
- `PERSONA_EDITOR_OPENAI_MODEL`
- `PERSONA_EDITOR_OPENAI_TIMEOUT_SECONDS`
- `PERSONA_EDITOR_OPENAI_TEMPERATURE`

`PERSONA_EDITOR_LLM_PROVIDER` 只能是 `openai`。本模块不读取旧 `OPENAI_*`，不读取 `LLM_PROVIDER`，不允许 `auto`、`mock` 或 `fallback`。

## finalize

模型只输出 patch JSON。后端合并 patch 到当前 `character.json`，生成 `preview_character_json`，校验通过后返回预览。

非法 JSON 直接 502。后端不会从 Markdown 或自然语言中截取 JSON，也不会自动修补 JSON。

patch 不允许修改 `id`、`display_name`、`avatar_url`、`voice`、`gptsovits_base_url`、`ref_audio_path`、`prompt_text`。

## apply

`apply` 必须由用户确认后才写入角色文件。写入前仍然走 `modules.characters` 校验。
