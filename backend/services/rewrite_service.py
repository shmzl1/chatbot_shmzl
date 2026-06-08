import re
from typing import Dict, List

from fastapi import HTTPException

from core.schemas import CharacterCard


class RewriteService:
    def rewrite_if_needed(
        self,
        *,
        character: CharacterCard,
        user_message: str,
        reply: str,
        score: Dict,
        need_rewrite: bool,
    ) -> tuple[str, bool]:
        if not need_rewrite:
            return reply, False

        rewritten = self._clean_service_tone(reply)
        rewritten = self._shorten(rewritten)

        if self._still_weak(rewritten):
            raise HTTPException(
                status_code=502,
                detail=(
                    "LLM reply failed style validation; "
                    "local rewrite cannot safely repair it; "
                    "no mock fallback is allowed."
                ),
            )

        return rewritten, rewritten != reply

    def _clean_service_tone(self, reply: str) -> str:
        replacements = {
            "很抱歉": "",
            "感谢您的理解": "",
            "如果您需要": "你要是还想说",
            "希望可以帮助到您": "",
            "作为AI": "",
            "作为 AI": "",
            "我是AI": "",
            "我是 AI": "",
            "语言模型": "",
            "扮演角色": "",
        }
        cleaned = reply.strip()
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or reply

    def _shorten(self, reply: str) -> str:
        parts: List[str] = [
            part.strip()
            for part in re.split(r"(?<=[。！？!?])", reply)
            if part.strip()
        ]
        if not parts:
            return reply.strip()

        shortened = "".join(parts[:3]).strip()
        if len(shortened) > 90:
            shortened = shortened[:88].rstrip("，,。.") + "。"
        return shortened

    def _still_weak(self, reply: str) -> bool:
        if len(reply.strip()) < 4:
            return True
        bad_markers = ("我是AI", "我是 AI", "语言模型", "很抱歉", "感谢您的")
        return any(marker in reply for marker in bad_markers)


rewrite_service = RewriteService()
