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
