# persona_review 模块

`persona_review` 负责人设编辑闭环。

## 桌面端闭环

桌面端聊天页通过“人设修正”入口接入本模块，不创建另一套接口。用户先从当前会话选择真实聊天轮次，逐条保存到：

```text
POST /feedback/persona/turn
```

保存内容包括 `character_id`、`session_id`、`turn_id`、用户消息、角色回复、评分、问题标签和说明。随后前端调用：

```text
POST /characters/{character_id}/persona-review/chat
POST /characters/{character_id}/persona-review/finalize
POST /characters/{character_id}/persona-review/apply
POST /characters/{character_id}/persona-review/rollback
```

人设编辑 AI 不是聊天角色本人，讨论不会写入普通聊天历史，不进入长期记忆或关系记忆。`finalize` 只生成 `preview_character_json` 和摘要；只有用户确认 apply 后才写入角色文件。`rollback` 只恢复最近一次备份。人设修正只影响后续回复，不改写历史聊天记录。

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

patch 只能修改可变补充人设，不能修改固定核心人设。

固定核心人设包括 `id`、`display_name`、`core_personality`、`speaking_style`、`relationship_to_user`、`forbidden`、`reply_patterns`、`lore`、`style_contract`。这些字段不能被 AI 自动修改、删除、覆盖或压缩。`avatar_url` 和 `voice` 是受保护元数据，也不能被人设编辑 AI 自动修改。

可变补充人设包括 `dialogues`、`reactions`、`bad_examples`、`evaluation_criteria`、`revision_notes`。finalize patch 只允许以下 key：

- `dialogues_append`
- `reactions_append`
- `bad_examples_append`
- `evaluation_criteria_append`
- `revision_note`

`revision_notes` 是 `character.json` 的真实字段；patch 中只能使用 `revision_note` 表示新增一条修订记录。

## apply

`apply` 必须由用户确认后才写入角色文件。写入前仍然走 `modules.characters` 校验。

用户确认 apply 后，后端只压缩可变补充字段：

- `dialogues` 最多 20 条
- `reactions` 最多 20 条
- `bad_examples` 最多 20 条
- `evaluation_criteria` 最多 30 条
- `revision_notes` 最多 20 条

`dialogues`、`reactions`、`bad_examples` 保留早期核心样例和最新样例；`evaluation_criteria` 去重后保留早期标准和最新标准；`revision_notes` 只保留最近 20 条。被裁剪内容追加到 `backups/persona_compaction_archive.jsonl`，生成 preview 时不写归档。
