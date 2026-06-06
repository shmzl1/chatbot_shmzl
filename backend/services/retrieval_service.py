import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from core.config import settings


RetrievalHit = Dict[str, Any]


class RetrievalService:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def retrieve(self, character_id: str, query: str) -> Dict[str, List[RetrievalHit]]:
        return {
            "lore": self._retrieve_from_jsonl(
                self.data_dir / "lore" / f"{character_id}_lore.jsonl",
                query,
                settings.top_k_lore,
                "lore",
            ),
            "dialogues": self._retrieve_from_jsonl(
                self.data_dir / "dialogues" / f"{character_id}_dialogues.jsonl",
                query,
                settings.top_k_dialogue,
                "dialogue",
            ),
            "reactions": self._retrieve_from_jsonl(
                self.data_dir / "reactions" / f"{character_id}_reactions.jsonl",
                query,
                settings.top_k_reaction,
                "reaction",
            ),
        }

    def used_ids(self, context: Dict[str, List[RetrievalHit]]) -> Dict[str, List[str]]:
        return {
            "used_lore": [str(hit["id"]) for hit in context.get("lore", [])],
            "used_dialogues": [str(hit["id"]) for hit in context.get("dialogues", [])],
            "used_reactions": [str(hit["id"]) for hit in context.get("reactions", [])],
        }

    def _retrieve_from_jsonl(
        self,
        file_path: Path,
        query: str,
        top_k: int,
        source: str,
    ) -> List[RetrievalHit]:
        if top_k <= 0 or not file_path.exists():
            return []

        documents = self._load_jsonl(file_path)
        scored: List[Tuple[int, int, Dict[str, Any], str]] = []
        for index, payload in enumerate(documents):
            text = self._flatten_text(payload)
            score = self._score(text, query)
            scored.append((score, index, payload, text))

        positive = [item for item in scored if item[0] > 0]
        chosen = positive if positive else scored[:top_k]
        chosen = sorted(chosen, key=lambda item: (-item[0], item[1]))[:top_k]

        hits: List[RetrievalHit] = []
        for score, _, payload, text in chosen:
            hits.append(
                {
                    "id": payload.get("id", ""),
                    "source": source,
                    "score": score,
                    "text": text,
                    "payload": payload,
                }
            )

        return hits

    def _load_jsonl(self, file_path: Path) -> List[Dict[str, Any]]:
        documents: List[Dict[str, Any]] = []
        with file_path.open("r", encoding="utf-8") as file:
            for line_no, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    item = {
                        "id": f"{file_path.stem}_{line_no}",
                        "content": line,
                    }
                if isinstance(item, dict):
                    documents.append(item)

        return documents

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


retrieval_service = RetrievalService(settings.data_dir)
