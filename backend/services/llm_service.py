import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from fastapi import HTTPException

from core.config import settings
from core.schemas import CandidateReply, CharacterCard


ALLOWED_EMOTIONS = {"neutral", "soft", "angry", "tired", "teasing", "serious"}
SUPPORTED_PROFILES = {"chat", "persona_editor"}
SUPPORTED_PROVIDERS = {"auto", "openai", "openai_compatible", "ark"}


@dataclass(frozen=True)
class LLMRuntimeConfig:
    profile: str
    provider: str
    api_key: str
    base_url: str
    model: str
    timeout_seconds: float
    temperature: float

    @property
    def provider_label(self) -> str:
        return "openai_compatible" if self.provider == "auto" else self.provider


@dataclass(frozen=True)
class LLMGeneration:
    candidates: List[CandidateReply]
    provider: str
    model: str | None
    profile: str
    raw_text: str | None = None


class LLMService:
    def generate_candidates(
        self,
        prompt: str,
        character: CharacterCard,
        user_message: str,
        profile: str = "chat",
    ) -> LLMGeneration:
        config = self.runtime_config(profile)
        return self._generate_with_openai(prompt, config)

    def generate_json(
        self,
        prompt: str,
        system_message: str,
        profile: str = "persona_editor",
    ) -> Dict[str, Any]:
        config = self.runtime_config(profile)
        raw_text = self._chat_completion(prompt, system_message, config)
        return self._load_json(raw_text, config)

    def runtime_config(self, profile: str) -> LLMRuntimeConfig:
        try:
            raw_config = settings.get_llm_config(profile)
        except ValueError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Unsupported LLM profile '{profile}'. "
                    f"Supported profiles: {', '.join(sorted(SUPPORTED_PROFILES))}."
                ),
            ) from exc

        normalized_profile = str(raw_config["profile"])
        if normalized_profile not in SUPPORTED_PROFILES:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Unsupported LLM profile '{normalized_profile}'. "
                    f"Supported profiles: {', '.join(sorted(SUPPORTED_PROFILES))}."
                ),
            )

        provider = str(raw_config["provider"] or "").strip().lower()
        if provider == "mock":
            raise HTTPException(
                status_code=500,
                detail=(
                    f"LLM provider 'mock' is disabled for profile '{normalized_profile}'. "
                    "Configure a real OpenAI-compatible API."
                ),
            )
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=500,
                detail=f"Unsupported LLM provider '{provider}' for profile '{normalized_profile}'.",
            )

        missing = []
        missing_labels = raw_config.get("missing_labels", {})
        if not raw_config.get("api_key"):
            missing.append(missing_labels.get("api_key", "api_key"))
        if not raw_config.get("base_url"):
            missing.append(missing_labels.get("base_url", "base_url"))
        if not raw_config.get("model"):
            missing.append(missing_labels.get("model", "model"))
        if missing:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"LLM configuration for profile '{normalized_profile}' is incomplete: "
                    f"{', '.join(missing)} is required."
                ),
            )

        return LLMRuntimeConfig(
            profile=normalized_profile,
            provider=provider,
            api_key=str(raw_config["api_key"]),
            base_url=str(raw_config["base_url"]),
            model=str(raw_config["model"]),
            timeout_seconds=float(raw_config["timeout_seconds"]),
            temperature=float(raw_config["temperature"]),
        )

    def _generate_with_openai(self, prompt: str, config: LLMRuntimeConfig) -> LLMGeneration:
        raw_text = self._chat_completion(prompt, "你是角色聊天回复生成器。你必须只输出 JSON。", config)
        candidates = self._parse_candidates(raw_text, config)
        return LLMGeneration(
            candidates=candidates,
            provider=config.provider_label,
            model=config.model,
            profile=config.profile,
            raw_text=raw_text,
        )

    def _chat_completion(
        self,
        prompt: str,
        system_message: str,
        config: LLMRuntimeConfig,
    ) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail="The openai package is not installed.",
            ) from exc

        client_kwargs: Dict[str, Any] = {
            "api_key": config.api_key,
            "timeout": config.timeout_seconds,
        }
        client_kwargs["base_url"] = config.base_url

        client = OpenAI(**client_kwargs)

        try:
            response = client.chat.completions.create(
                model=config.model,
                temperature=config.temperature,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"LLM request failed for profile '{config.profile}' "
                    f"with model '{config.model}': {exc}"
                ),
            ) from exc

        return response.choices[0].message.content or ""

    def _parse_candidates(self, raw_text: str, config: LLMRuntimeConfig) -> List[CandidateReply]:
        data = self._load_json(raw_text, config)
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

    def _load_json(self, raw_text: str, config: LLMRuntimeConfig) -> Dict[str, Any]:
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
                detail=(
                    f"LLM response for profile '{config.profile}' "
                    f"with model '{config.model}' is not valid JSON: {exc}"
                ),
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


def provider_label(profile: str = "chat") -> str:
    return llm_service.runtime_config(profile).provider_label
