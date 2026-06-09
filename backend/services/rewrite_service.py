from typing import Dict

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

        raise HTTPException(
            status_code=502,
            detail=(
                "LLM reply failed style validation; "
                "local repair is disabled and no simulated reply is allowed."
            ),
        )


rewrite_service = RewriteService()
