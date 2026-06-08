# persona_review 模块

`persona_review` 模块负责人设编辑闭环。

## 职责

- 接收用户选中的聊天片段。
- 记录用户对角色回复的评价。
- 与人设编辑 AI 多轮讨论修改方向。
- 生成最终修改方案。
- 生成 `preview_character_json`。
- 在用户确认后应用修改。
- 支持上一版人设回滚。

## 安全流程

```text
chat      只讨论，不写文件
finalize  只生成预览，不写文件
apply     校验后写入 character.json
rollback  恢复上一版备份
```

## 人物依赖

读取和写入角色包必须通过 `modules.characters`。

不要在本模块中重新拼接人物包路径。

## 注意事项

- 不要让 `chat` 或 `finalize` 写入角色包。
- 不要绕过角色包校验。
- 不要修改受保护字段。
- LLM 失败时返回明确错误。
