# relationship_memory 模块

`relationship_memory` 管理用户和角色之间的长期关系上下文。

## 数据表

迁移文件：

```text
backend/database/migrations/006_create_relationship_memory_events.sql
```

表名：

```text
relationship_memory_events
```

核心字段包括 `character_id`、`source_type`、`source_id`、`source_turn_id`、`memory_type`、`content`、`evidence`、`importance`、`is_active`、`created_at`、`updated_at`。

## 接口

```text
POST /relationship-memory
GET /relationship-memory?character_id=role01
POST /relationship-memory/{event_id}/deactivate
GET /relationship-memory/debug?character_id=role01
```

## 聊天接入

普通聊天会读取当前角色的有效关系记忆，并加入 prompt 的“关系长期上下文”区域。

旧 `long_term_memories` 仍然保留。前端确认聊天记忆建议时，会继续写入 `/memory`，并额外写入 `/relationship-memory`。

## 注意事项

- 停用关系记忆只更新 `is_active = false`，不物理删除事件。
- 不要把共享关系记忆写进某个单独角色包。
- 当前阶段不要新增日程、日记、QQ/微信接入或云部署能力。
