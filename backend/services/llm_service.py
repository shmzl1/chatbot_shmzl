import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from fastapi import HTTPException

from core.config import settings
from core.schemas import CandidateReply, CharacterCard


ALLOWED_EMOTIONS = {"neutral", "soft", "angry", "tired", "teasing", "serious"}


@dataclass(frozen=True)
class LLMGeneration:
    candidates: List[CandidateReply]
    provider: str
    model: str | None
    raw_text: str | None = None


class LLMService:
    def generate_candidates(
        self,
        prompt: str,
        character: CharacterCard,
        user_message: str,
    ) -> LLMGeneration:
        self._validate_llm_settings()
        return self._generate_with_openai(prompt)

    def _validate_llm_settings(self) -> None:
        provider = settings.llm_provider.lower()
        if provider == "mock":
            raise HTTPException(
                status_code=500,
                detail="LLM_PROVIDER=mock is disabled. Configure a real OpenAI-compatible API.",
            )
        if provider not in {"auto", "openai", "openai_compatible", "ark"}:
            raise HTTPException(
                status_code=500,
                detail=f"Unsupported LLM_PROVIDER '{settings.llm_provider}'.",
            )

        missing = []
        if not settings.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not settings.openai_model:
            missing.append("OPENAI_MODEL")
        if not settings.openai_base_url:
            missing.append("OPENAI_BASE_URL")
        if missing:
            raise HTTPException(
                status_code=500,
                detail=f"LLM configuration is incomplete: {', '.join(missing)} is required.",
            )

    def _generate_with_openai(self, prompt: str) -> LLMGeneration:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail="The openai package is not installed.",
            ) from exc

        client_kwargs: Dict[str, Any] = {
            "api_key": settings.openai_api_key,
            "timeout": settings.openai_timeout_seconds,
        }
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url

        client = OpenAI(**client_kwargs)

        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                temperature=settings.openai_temperature,
                messages=[
                    {
                        "role": "system",
                        "content": "你是角色聊天回复生成器。你必须只输出 JSON。",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"LLM request failed: {exc}",
            ) from exc

        raw_text = response.choices[0].message.content or ""
        candidates = self._parse_candidates(raw_text)
        return LLMGeneration(
            candidates=candidates,
            provider=provider_label(),
            model=settings.openai_model,
            raw_text=raw_text,
        )

    def _parse_candidates(self, raw_text: str) -> List[CandidateReply]:
        data = self._load_json(raw_text)
        raw_candidates = data.get("candidates")
        if not isinstance(raw_candidates, list) or not raw_candidates:
            raise HTTPException(
                status_code=502,
                detail="LLM response JSON does not contain a valid candidates list.",
            )

        candidates: List[CandidateReply] = []
        for item in raw_candidates[:3]:
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=502,
                    detail="LLM candidate item must be an object.",
                )

            reply = str(item.get("reply", "")).strip()
            if not reply:
                raise HTTPException(
                    status_code=502,
                    detail="LLM candidate reply is empty.",
                )

            emotion = str(item.get("emotion", "neutral")).strip()
            if emotion not in ALLOWED_EMOTIONS:
                raise HTTPException(
                    status_code=502,
                    detail=f"LLM candidate emotion '{emotion}' is not allowed.",
                )

            candidates.append(
                CandidateReply(
                    reply=reply,
                    emotion=emotion,
                    reason=str(item.get("reason", "")).strip(),
                )
            )

        return candidates

    def _load_json(self, raw_text: str) -> Dict[str, Any]:
        text = raw_text.strip()
        fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()
        else:
            text = self._extract_json_object(text)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"LLM response is not valid JSON: {exc}",
            ) from exc

        if not isinstance(data, dict):
            raise HTTPException(
                status_code=502,
                detail="LLM response JSON root must be an object.",
            )

        return data

    def _extract_json_object(self, text: str) -> str:
        if text.startswith("{") and text.endswith("}"):
            return text

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return text[start : end + 1]
        return text


def provider_label() -> str:
    provider = settings.llm_provider.lower()
    return "openai_compatible" if provider == "auto" else provider


llm_service = LLMService()
