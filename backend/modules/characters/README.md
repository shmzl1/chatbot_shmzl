# characters 模块

`characters` 是角色系统唯一入口。角色读取、校验、头像、角色包创建、更新、删除和恢复都通过本模块完成。

## 角色包

```text
backend/modules/characters/packs/{character_id}/
  character.json
  voice_refs/
  backups/
```

`character.json` 是必需文件。`voice_refs/` 保存该角色的语音参考素材。`backups/` 保存上一版角色文件。

## 约束

- 其他模块需要角色信息时，直接调用 `modules.characters.service`。
- 不从旧角色目录读取角色包。
- 写入前必须校验。
- 角色 JSON 非法直接报错。
- GPT-SoVITS 的 `prompt_text` 可以为空。

## 人设字段分层

当前 `character.json` 分为固定核心人设和可变补充人设。

固定核心人设包括：

- `id`
- `display_name`
- `core_personality`
- `speaking_style`
- `relationship_to_user`
- `forbidden`
- `reply_patterns`
- `lore`
- `style_contract`

这些字段不可被人设编辑 AI 自动修改、删除、覆盖或压缩；聊天 prompt 每次必须完整读取。`avatar_url` 和 `voice` 是受保护元数据，也不可被人设编辑 AI 自动修改。

可变补充人设包括：

- `dialogues`
- `reactions`
- `bad_examples`
- `evaluation_criteria`
- `revision_notes`

这些字段可以由人设编辑 AI 少量追加，并在用户确认 apply 后按上限压缩。裁剪内容归档到 `backups/persona_compaction_archive.jsonl`。
