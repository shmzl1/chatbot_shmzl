# diary 模块

`diary` 负责本地单用户日记 MVP：日记 CRUD、图片附件元数据、软删除，以及用户主动选择某篇日记后的聊天上下文构造。

## 数据边界

- 日记正文保存在 PostgreSQL 的 `diary_entries`。
- 图片文件保存到 `uploads/diary/images/`，数据库只保存文件名、路径、URL、MIME 和大小，不保存 base64。
- 删除日记或图片只做软删除。

## 聊天边界

聊天默认不会读取任何日记。只有前端传入明确的 `diary_entry_id` 时，`modules.diary.context` 才会读取该篇日记并加入 prompt 的“用户主动提供的日记上下文”。

日记不会自动写入长期记忆。若未来要把日记内容变成关系记忆，必须走用户确认流程。

## 接口

- `GET /diary/entries`
- `POST /diary/entries`
- `GET /diary/entries/{entry_id}`
- `PUT /diary/entries/{entry_id}`
- `DELETE /diary/entries/{entry_id}`
- `POST /diary/entries/{entry_id}/images`
- `DELETE /diary/images/{image_id}`
