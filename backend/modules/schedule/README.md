# schedule 模块

`schedule` 是本地 SQLite 日程模块，第一阶段 MVP 已实现。

## 第一阶段职责

- 创建、读取、更新、软删除任务。
- 查询某一天的任务列表。
- 查询月历中每天的任务数量和状态。
- 完成、跳过、延期待处理或已逾期的任务实例。
- 保存任务类型、优先级、标签和预计用时。

## 数据表

SQLite migration `002_add_schedule_mvp.sql` 新增：

- `schedule_items`：任务主体，按 `user_id` 归属本地用户，删除使用 `is_deleted` 软删除。
- `schedule_occurrences`：任务实例，保存安排日期、时间、状态和延期来源。
- `schedule_completion_logs`：完成、跳过、延期操作日志。

第一阶段没有创建 `schedule_plans`。计划管理、自动复习和 AI 排程属于第二阶段。

## 接口

```text
GET    /schedule/items
POST   /schedule/items
GET    /schedule/items/{item_id}
PUT    /schedule/items/{item_id}
DELETE /schedule/items/{item_id}
GET    /schedule/today
GET    /schedule/calendar
POST   /schedule/occurrences/{occurrence_id}/complete
POST   /schedule/occurrences/{occurrence_id}/skip
POST   /schedule/occurrences/{occurrence_id}/postpone
```

## 状态迁移

- `pending -> done`
- `pending -> skipped`
- `pending -> postponed`，并创建新的 `pending` occurrence
- `overdue -> done`
- `overdue -> skipped`
- `overdue -> postponed`，并创建新的 `pending` occurrence

`done`、`skipped`、`postponed` 等终态实例再次操作会返回 409。

## 边界

日程默认不会进入聊天 prompt，不会自动写入长期记忆，也不会让角色自动修改日程。
