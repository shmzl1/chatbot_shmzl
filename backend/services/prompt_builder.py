import json
from typing import Any, Dict, Iterable, List

from core.schemas import CharacterCard


def _lines(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    if not values:
        return "- 未配置"

    return "\n".join(f"- {item}" for item in values)


def _format_hits(hits: List[Dict[str, Any]], field_names: Iterable[str]) -> str:
    if not hits:
        return "- 未检索到相关资料"

    lines = []
    for hit in hits:
        payload = hit.get("payload", {})
        title = payload.get("title") or payload.get("scene") or payload.get("situation") or hit.get("id")
        details = []
        for field_name in field_names:
            value = payload.get(field_name)
            if value:
                details.append(f"{field_name}: {value}")
        detail_text = "；".join(details) if details else hit.get("text", "")
        lines.append(f"- [{hit.get('id')}] {title}：{detail_text}")

    return "\n".join(lines)


def _format_history(history: List[Dict[str, str]]) -> str:
    if not history:
        return "- 无"

    lines = []
    for item in history:
        lines.append(f"- 用户：{item.get('user', '')}")
        lines.append(f"  角色：{item.get('assistant', '')}")
    return "\n".join(lines)


def build_chat_prompt(
    character: CharacterCard,
    user_message: str,
    retrieval_context: Dict[str, List[Dict[str, Any]]] | None = None,
) -> str:
    reply_patterns = json.dumps(
        character.reply_patterns,
        ensure_ascii=False,
        indent=2,
    )
    retrieval_context = retrieval_context or {}
    lore_hits = retrieval_context.get("lore", [])
    dialogue_hits = retrieval_context.get("dialogues", [])
    reaction_hits = retrieval_context.get("reactions", [])
    memory_hits = retrieval_context.get("memories", [])
    relationship_memory_hits = retrieval_context.get("relationship_memories", [])
    history = retrieval_context.get("history", [])

    return f"""请根据角色卡，为用户输入生成 3 个候选回复。

角色 ID：{character.id}
角色名：{character.display_name}

核心性格：
{_lines(character.core_personality)}

说话风格：
{_lines(character.speaking_style)}

与用户关系：
{character.relationship_to_user or "未配置"}

禁用规则：
{_lines(character.forbidden)}

回复模式：
{reply_patterns}

相关背景故事：
{_format_hits(lore_hits, ("content", "tags"))}

相似说话规律：
{_format_hits(dialogue_hits, ("style_summary", "rewrite_rule", "emotion", "intent"))}

当前场景反应规则：
{_format_hits(reaction_hits, ("reaction", "reply_pattern", "avoid"))}

长期记忆：
{_format_hits(memory_hits, ("content", "memory_type", "importance", "tags"))}

关系长期上下文：
{_format_hits(relationship_memory_hits, ("content", "memory_type", "importance", "source_type", "evidence"))}

最近聊天历史：
{_format_history(history)}

用户输入：
{user_message}

要求：
1. 不要说自己是 AI。
2. 不要说自己在扮演角色。
3. 不要复读原始台词。
4. 回复要短，适合后续 TTS 朗读。
5. 生成 3 个不同候选，emotion 只能从 neutral、soft、angry、tired、teasing、serious 中选择。
6. 只输出严格 JSON，不要输出 Markdown。

输出格式：
{{
  "candidates": [
    {{
      "reply": "候选回复文本",
      "emotion": "soft",
      "reason": "为什么符合角色"
    }}
  ]
}}
"""
