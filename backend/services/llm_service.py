import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from fastapi import HTTPException

from core.config import settings
from core.schemas import CandidateReply, CharacterCard
from services.character_service import character_service


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
        if self._should_use_openai():
            return self._generate_with_openai(prompt)

        return self._generate_with_mock(character, user_message)

    def _should_use_openai(self) -> bool:
        provider = settings.llm_provider.lower()
        if provider == "mock":
            return False

        if provider in {"openai", "openai_compatible", "ark"}:
            if not settings.openai_api_key:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM_PROVIDER={settings.llm_provider} but OPENAI_API_KEY is empty.",
                )
            if not settings.openai_model:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM_PROVIDER={settings.llm_provider} but OPENAI_MODEL is empty.",
                )
            return True

        if provider == "auto":
            return bool(settings.openai_api_key and settings.openai_model)

        raise HTTPException(
            status_code=500,
            detail=f"Unsupported LLM_PROVIDER '{settings.llm_provider}'.",
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
            provider="openai",
            model=settings.openai_model,
            raw_text=raw_text,
        )

    def _generate_with_mock(
        self,
        character: CharacterCard,
        user_message: str,
    ) -> LLMGeneration:
        first_reply = character_service.build_mock_reply(character, user_message)
        candidates = [
            CandidateReply(
                reply=first_reply,
                emotion=character.voice.default_emotion,
                reason="本地 mock：根据关键词和角色卡生成。",
            ),
            CandidateReply(
                reply="别把事情憋成一团。挑最麻烦的那块说，我听着。",
                emotion="soft",
                reason="短句、嘴硬，但保留陪伴感。",
            ),
            CandidateReply(
                reply="行了，先停一下。你现在需要的是办法，不是继续吓自己。",
                emotion="serious",
                reason="更直接，适合用户情绪较重的场景。",
            ),
        ]
        return LLMGeneration(candidates=candidates, provider="mock", model=None)

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
                continue

            reply = str(item.get("reply", "")).strip()
            if not reply:
                continue

            emotion = str(item.get("emotion", "neutral")).strip()
            if emotion not in ALLOWED_EMOTIONS:
                emotion = "neutral"

            candidates.append(
                CandidateReply(
                    reply=reply,
                    emotion=emotion,
                    reason=str(item.get("reason", "")).strip(),
                )
            )

        if not candidates:
            raise HTTPException(
                status_code=502,
                detail="LLM response did not provide any usable candidate replies.",
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
                detail="LLM response is not valid JSON.",
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


llm_service = LLMService()
