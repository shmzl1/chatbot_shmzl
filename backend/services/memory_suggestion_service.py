import re
from typing import Dict, List


class MemorySuggestionService:
    def suggest(self, *, user_message: str) -> List[Dict]:
        suggestions: List[Dict] = []
        text = user_message.strip()
        self._maybe_add_explicit_memory(text, suggestions)
        self._maybe_add_name(text, suggestions)
        self._maybe_add_preference(text, suggestions)
        self._maybe_add_dislike(text, suggestions)
        self._maybe_add_recurring_state(text, suggestions)
        return suggestions[:3]

    def _maybe_add_explicit_memory(self, text: str, suggestions: List[Dict]) -> None:
        match = re.search(r"(?:请|帮我)?记住[:：，, ]?(.{2,80})", text)
        if not match:
            return
        content = match.group(1).strip("。！？!?,， ")
        if content:
            suggestions.append(
                {
                    "memory_type": "note",
                    "content": f"用户要求记住：{content}",
                    "importance": 8,
                    "tags": ["用户要求", "长期记忆"],
                }
            )

    def _maybe_add_name(self, text: str, suggestions: List[Dict]) -> None:
        match = re.search(r"我(?:叫|是)([^，。！？\s]{1,16})", text)
        if not match:
            return
        name = match.group(1).strip()
        if any(word in name for word in ("废物", "没用", "笨蛋", "失败", "傻")):
            return
        if name:
            suggestions.append(
                {
                    "memory_type": "profile",
                    "content": f"用户希望被称呼为：{name}",
                    "importance": 8,
                    "tags": ["称呼", "用户信息"],
                }
            )

    def _maybe_add_preference(self, text: str, suggestions: List[Dict]) -> None:
        match = re.search(r"我喜欢([^，。！？]{1,32})", text)
        if not match:
            return
        value = match.group(1).strip()
        if value:
            suggestions.append(
                {
                    "memory_type": "preference",
                    "content": f"用户喜欢：{value}",
                    "importance": 6,
                    "tags": ["偏好"],
                }
            )

    def _maybe_add_dislike(self, text: str, suggestions: List[Dict]) -> None:
        match = re.search(r"我(?:不喜欢|讨厌)([^，。！？]{1,32})", text)
        if not match:
            return
        value = match.group(1).strip()
        if value:
            suggestions.append(
                {
                    "memory_type": "preference",
                    "content": f"用户不喜欢：{value}",
                    "importance": 6,
                    "tags": ["偏好", "避开"],
                }
            )

    def _maybe_add_recurring_state(self, text: str, suggestions: List[Dict]) -> None:
        if "经常" not in text and "最近" not in text and "总是" not in text:
            return
        if any(word in text for word in ("睡不着", "失眠", "很累", "焦虑", "考砸", "不想学习")):
            suggestions.append(
                {
                    "memory_type": "state",
                    "content": f"用户提到近期状态：{text[:80]}",
                    "importance": 7,
                    "tags": ["近期状态", "关心点"],
                }
            )


memory_suggestion_service = MemorySuggestionService()
