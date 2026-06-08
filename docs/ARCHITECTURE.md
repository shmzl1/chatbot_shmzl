# 架构说明

本文档描述当前虚拟人物陪伴系统的主要结构。

## 总体结构

项目由后端、前端、数据库和本地素材组成。

```text
frontend/simple_web
        |
        v
backend/main.py
        |
        v
backend/modules/*
        |
        v
PostgreSQL + 本地人物包
```

后端使用 FastAPI。
前端当前是简单网页。
数据库保存结构化数据。
人物包以文件夹形式保存在项目中。

## 后端模块

后端模块位于：

```text
backend/modules/
```

当前主要模块：

- `auth`：登录和本地用户保护。
- `chat`：普通聊天入口。
- `characters`：人物包管理。
- `persona_review`：人设编辑闭环。
- `memory`：长期记忆。
- `knowledge`：知识库。
- `voice`：语音调用。
- `debug`：调试接口。
- `relationship_memory`：共享关系记忆预留。
- `schedule`：日程预留。
- `diary`：日记预留。
- `health`：健康检查。

## 人物包

人物包统一放在：

```text
backend/modules/characters/packs/
```

每个角色一个目录：

```text
packs/{character_id}/
  character.json
  voice_refs/
  backups/
```

`character.json` 是角色的核心数据文件。

旧目录 `backend/data/character_packs` 已废弃。
新代码不应依赖旧目录。

## 数据流

普通聊天流程：

```text
前端
  -> chat API
  -> characters 模块读取角色
  -> retrieval / memory / LLM
  -> 保存聊天记录
  -> 返回文本和可选语音
```

人设编辑流程：

```text
选中聊天片段
  -> persona-review/chat
  -> persona-review/finalize
  -> 生成 preview_character_json
  -> persona-review/apply
  -> characters 模块校验并写入角色包
```

## 数据库存储

PostgreSQL 保存以下数据：

- 本地用户。
- 聊天会话。
- 聊天轮次。
- 长期记忆。
- 知识库条目。
- 人设反馈。
- 头像映射兼容数据。

人物包本身不放在数据库中。

## 文件写入原则

人物包写入必须满足：

- 先写临时文件。
- 校验通过后再原子替换。
- 覆盖前备份上一版。
- 删除时移动到 `.trash`。
- 失败时不覆盖原文件。

## 可选语音

语音模块可以调用 GPT-SoVITS。

语音配置来自当前角色包的 `voice` 字段。
相对参考音频路径应相对于角色包目录解析。

语音不可用时，不应破坏普通文字聊天。
