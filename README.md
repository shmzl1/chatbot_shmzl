# 虚拟人物陪伴系统

本项目是本地运行的虚拟人物聊天系统。运行入口集中在 `backend/modules/*`，角色读取、校验、头像和角色包管理都走 `backend/modules/characters`。

## 当前结构

```text
backend/
  main.py
  core/
  modules/
    characters/
    chat/
    persona_review/
    voice/
    auth/
    health/
    debug/
    memory/
    knowledge/
  services/
  database/
frontend/simple_web/
docs/
```

普通聊天接口路径保持不变：

```text
POST /chat/text
POST /chat
```

人设编辑接口路径保持不变：

```text
POST /characters/{character_id}/persona-review/chat
POST /characters/{character_id}/persona-review/finalize
POST /characters/{character_id}/persona-review/apply
POST /characters/{character_id}/persona-review/rollback
```

## LLM 配置

普通聊天只读取 `CHAT_*`：

```env
CHAT_LLM_PROVIDER="openai"
CHAT_OPENAI_API_KEY=""
CHAT_OPENAI_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
CHAT_OPENAI_MODEL="doubao-seed-character-251128"
CHAT_OPENAI_TIMEOUT_SECONDS="120"
CHAT_OPENAI_TEMPERATURE="0.8"
```

人设编辑只读取 `PERSONA_EDITOR_*`：

```env
PERSONA_EDITOR_LLM_PROVIDER="openai"
PERSONA_EDITOR_OPENAI_API_KEY=""
PERSONA_EDITOR_OPENAI_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
PERSONA_EDITOR_OPENAI_MODEL="doubao-seed-2-0-pro-260215"
PERSONA_EDITOR_OPENAI_TIMEOUT_SECONDS="180"
PERSONA_EDITOR_OPENAI_TEMPERATURE="0.2"
```

项目不读取旧 `OPENAI_*` 配置，不读取 `LLM_PROVIDER`，不允许 `auto`、`mock` 或 `fallback`。缺配置、模型请求失败、模型超时、JSON 非法都会直接报错。

## 人设编辑

`finalize` 只接受模型输出 patch JSON。后端把 patch 合并到当前 `character.json`，生成 `preview_character_json`，校验通过后返回预览。

`apply` 必须由用户确认后才写入。patch 不允许修改 `id`、`display_name`、`avatar_url`、`voice`、`gptsovits_base_url`、`ref_audio_path`、`prompt_text`。模型返回非法 JSON 时直接返回 502，不做自动修补。

## 语音规则

GPT-SoVITS 的 `prompt_text` 可以为空。`neutral` 是默认语音参考：用户没有明确选择 emotion 时使用 `neutral`。

用户明确选择 `angry`、`sad`、`happy` 等 emotion 时，必须存在该 emotion 的参考音频；缺少对应 `ref_audio_path` 会直接报错，不会退回 `neutral`。

## 轻量检查

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m compileall .
```
