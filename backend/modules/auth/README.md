# auth 模块

`auth` 模块只负责本地默认用户，不提供注册、密码登录、JWT 或 Bearer Token 登录锁。

## 本地默认用户

- 后端启动或首次调用 `/auth/me` 时，会自动确保 `users` 表里存在一个默认本地用户。
- 如果没有用户，创建用户名为 `我` 的本地用户，密码哈希为空字符串。
- 如果已经有一个用户，直接复用。
- 如果发现多个用户，直接报错，要求手动检查数据库。

## 接口

```text
GET  /auth/status
GET  /auth/me
PUT  /auth/me
POST /auth/me/avatar
POST /auth/logout
```

`/auth/logout` 只返回 `ok`，不会退出本地默认用户。

## 边界

- `get_current_user` 保留函数名，供聊天、日记、记忆、知识库等接口继续依赖，但它直接返回默认本地用户。
- 用户可修改的是 `username`，不要修改 `users.id`。
- 用户头像仍通过 `/auth/me/avatar` 上传到项目已有 uploads 目录。
- 不要把本地用户信息写入人物包。
