# relationship_memory 模块

`relationship_memory` 管理用户和角色之间的长期关系上下文。

## 数据表

SQLite 迁移文件：

```text
backend/database/sqlite_migrations/001_create_sqlite_schema.sql
```

表名：

```text
relationship_memory_events
```

核心字段包括 `character_id`、`source_type`、`source_id`、`source_turn_id`、`memory_type`、`content`、`evidence`、`importance`、`is_active`、`is_pinned`、`is_editable`、`read_policy`、`status`、`expires_at`、`last_used_at`、`use_count`、`created_at`、`updated_at`。JSON 字段在 SQLite 中以 TEXT 保存 JSON 字符串，布尔字段以 INTEGER 0/1 保存。

## 接口

```text
POST /relationship-memory
GET /relationship-memory?character_id=role01
POST /relationship-memory/{event_id}/deactivate
GET /relationship-memory/debug?character_id=role01
```

## 聊天接入

普通聊天会读取当前角色的关系记忆，并按分层规则加入 prompt：

- pinned / always_read：`is_pinned=true` 或 `read_policy=always`，每次必读，不参与 topK。
- 普通 active：`status=active`、`read_policy=relevant`、未过期，按重要度 topK 进入 prompt。
- 短期记忆：设置 `expires_at` 后，过期不再进入 prompt。

`archived`、`superseded`、`deleted`、`read_policy=never`、已过期或 `is_active=false` 的关系记忆不会进入 prompt。

旧 `long_term_memories` 仍然保留。前端确认聊天记忆建议时，会继续写入 `/memory`，并额外写入 `/relationship-memory`。

## 注意事项

- 停用关系记忆只更新 `is_active = false`，不物理删除事件。
- 不要把共享关系记忆写进某个单独角色包。
- pinned 关系记忆只能由用户未来在管理界面显式维护，AI 不应自动删除或覆盖。
- 当前阶段不要新增日程、日记、QQ/微信接入或云部署能力。
