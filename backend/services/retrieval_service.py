import re
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException

from core.config import settings
from services.character_service import character_service


RetrievalHit = Dict[str, Any]


class RetrievalService:
    def retrieve(self, character_id: str, query: str) -> Dict[str, List[RetrievalHit]]:
        character = character_service.get_character(character_id)
        return {
            "lore": self._retrieve_from_items(
                character.lore,
                query,
                settings.top_k_lore,
                "lore",
                character.id,
            ),
            "dialogues": self._retrieve_from_items(
                character.dialogues,
                query,
                settings.top_k_dialogue,
                "dialogue",
                character.id,
            ),
            "reactions": self._retrieve_from_items(
                character.reactions,
                query,
                settings.top_k_reaction,
                "reaction",
                character.id,
            ),
        }

    def used_ids(self, context: Dict[str, List[RetrievalHit]]) -> Dict[str, List[str]]:
        return {
            "used_lore": [str(hit["id"]) for hit in context.get("lore", [])],
            "used_dialogues": [str(hit["id"]) for hit in context.get("dialogues", [])],
            "used_reactions": [str(hit["id"]) for hit in context.get("reactions", [])],
        }

    def _retrieve_from_items(
        self,
        items: List[Dict[str, Any]],
        query: str,
        top_k: int,
        source: str,
        character_id: str,
    ) -> List[RetrievalHit]:
        if top_k <= 0:
            return []
        if not isinstance(items, list):
            raise HTTPException(
                status_code=500,
                detail=f"Character pack '{character_id}' field for {source} must be an array.",
            )

        scored: List[Tuple[int, int, Dict[str, Any], str]] = []
        for index, payload in enumerate(items):
            if not isinstance(payload, dict):
                raise HTTPException(
                    status_code=500,
                    detail=f"Character pack '{character_id}' {source}[{index}] must be an object.",
                )
            text = self._flatten_text(payload)
            score = self._score(text, query)
            scored.append((score, index, payload, text))

        positive = [item for item in scored if item[0] > 0]
        chosen = positive if positive else scored
        chosen = sorted(chosen, key=lambda item: (-item[0], item[1]))[:top_k]

        return [
            {
                "id": payload.get("id", ""),
                "source": source,
                "score": score,
                "text": text,
                "payload": payload,
            }
            for score, _, payload, text in chosen
        ]

    def _score(self, text: str, query: str) -> int:
        haystack = self._normalize(text)
        terms = self._terms(query)
        score = 0
        for term in terms:
            if term in haystack:
                score += len(term) + haystack.count(term)
        return score

    def _terms(self, text: str) -> List[str]:
        normalized = self._normalize(text)
        chunks = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]+", normalized)
        terms = set()

        for chunk in chunks:
            if len(chunk) <= 1:
                continue
            terms.add(chunk)
            if re.fullmatch(r"[\u4e00-\u9fff]+", chunk):
                for size in (2, 3, 4):
                    for index in range(0, max(len(chunk) - size + 1, 0)):
                        terms.add(chunk[index : index + size])

        return sorted(terms, key=lambda item: (-len(item), item))

    def _flatten_text(self, value: Any) -> str:
        if isinstance(value, dict):
            return " ".join(self._flatten_text(item) for item in value.values())
        if isinstance(value, list):
            return " ".join(self._flatten_text(item) for item in value)
        return str(value)

    def _normalize(self, text: str) -> str:
        return text.lower().strip()


retrieval_service = RetrievalService()
