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

## LLM profile

人设编辑使用 `persona_editor` profile。

配置项为：

- `PERSONA_EDITOR_LLM_PROVIDER`
- `PERSONA_EDITOR_OPENAI_API_KEY`
- `PERSONA_EDITOR_OPENAI_BASE_URL`
- `PERSONA_EDITOR_OPENAI_MODEL`
- `PERSONA_EDITOR_OPENAI_TIMEOUT_SECONDS`
- `PERSONA_EDITOR_OPENAI_TEMPERATURE`

人设编辑只读取 `PERSONA_EDITOR_*` 配置。
项目不保留旧 `OPENAI_*` 兼容机制。
如果这些配置缺失，人设编辑接口会直接报错。

人设编辑 AI 不是当前角色本人。
它只分析、讨论和生成方案，未经用户确认不能写入 `character.json`。

## 注意事项

- 不要让 `chat` 或 `finalize` 写入角色包。
- 不要绕过角色包校验。
- 不要修改受保护字段。
- 不要使用普通聊天模型配置做人设编辑。
- 不要使用 `LLM_PROVIDER=auto` 或 mock provider。
- LLM 失败时返回明确错误。
