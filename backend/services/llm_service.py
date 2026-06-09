import json
from dataclasses import dataclass
from typing import Any, Dict, List

from fastapi import HTTPException

from core.config import settings
from core.schemas import CandidateReply, CharacterCard


ALLOWED_EMOTIONS = {"neutral", "soft", "angry", "tired", "teasing", "serious"}
SUPPORTED_PROFILES = {"chat", "persona_editor"}
SUPPORTED_PROVIDERS = {"openai"}
PROFILE_LABELS = {
    "chat": "chat",
    "persona_editor": "persona_editor",
}


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
        return self.provider


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
        raw_text = self._chat_completion(
            prompt,
            "You generate character chat replies. Return a strict JSON object only.",
            config,
        )
        candidates = self._parse_candidates(raw_text, config)
        return LLMGeneration(
            candidates=candidates,
            provider=config.provider_label,
            model=config.model,
            profile=config.profile,
            raw_text=raw_text,
        )

    def generate_json(
        self,
        prompt: str,
        system_message: str,
        profile: str = "persona_editor",
        strict_json: bool = False,
    ) -> Dict[str, Any]:
        config = self.runtime_config(profile)
        raw_text = self._chat_completion(
            prompt,
            system_message,
            config,
            strict_json=strict_json,
        )
        return self._load_json(raw_text, config)

    def runtime_config(self, profile: str) -> LLMRuntimeConfig:
        try:
            raw_config = settings.get_llm_config(profile)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        normalized_profile = str(raw_config["profile"])
        if normalized_profile not in SUPPORTED_PROFILES:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Unsupported LLM profile '{normalized_profile}'. "
                    f"Supported profiles: {', '.join(sorted(SUPPORTED_PROFILES))}."
                ),
            )

        missing_labels = raw_config.get("missing_labels", {})
        provider = str(raw_config["provider"] or "").strip().lower()
        if not provider:
            raise HTTPException(
                status_code=500,
                detail=self._missing_config_detail(
                    normalized_profile,
                    [missing_labels.get("provider", "provider")],
                ),
            )
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Unsupported LLM provider '{provider}' for profile '{normalized_profile}'. "
                    "Only 'openai' is allowed."
                ),
            )

        missing = []
        if not raw_config.get("api_key"):
            missing.append(missing_labels.get("api_key", "api_key"))
        if not raw_config.get("base_url"):
            missing.append(missing_labels.get("base_url", "base_url"))
        if not raw_config.get("model"):
            missing.append(missing_labels.get("model", "model"))
        if raw_config.get("timeout_seconds") is None:
            missing.append(missing_labels.get("timeout_seconds", "timeout_seconds"))
        if raw_config.get("temperature") is None:
            missing.append(missing_labels.get("temperature", "temperature"))
        if missing:
            raise HTTPException(
                status_code=500,
                detail=self._missing_config_detail(normalized_profile, missing),
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

    def _chat_completion(
        self,
        prompt: str,
        system_message: str,
        config: LLMRuntimeConfig,
        strict_json: bool = False,
    ) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail="The openai package is not installed.",
            ) from exc

        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )
        request_kwargs: Dict[str, Any] = {
            "model": config.model,
            "temperature": config.temperature,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
        }
        if strict_json:
            request_kwargs["response_format"] = {"type": "json_object"}

        try:
            response = client.chat.completions.create(**request_kwargs)
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
        try:
            data = json.loads(raw_text.strip())
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"LLM response is not valid JSON; profile='{config.profile}'; "
                    f"model='{config.model}'; parse_error='{exc}'"
                ),
            ) from exc

        if not isinstance(data, dict):
            raise HTTPException(
                status_code=502,
                detail=(
                    f"LLM response JSON root must be an object; "
                    f"profile='{config.profile}'; model='{config.model}'"
                ),
            )

        return data

    def _missing_config_detail(self, profile: str, fields: List[str]) -> str:
        profile_label = PROFILE_LABELS.get(profile, profile)
        return f"Missing LLM config for {profile_label}: {', '.join(fields)}"


llm_service = LLMService()


def provider_label(profile: str = "chat") -> str:
    return llm_service.runtime_config(profile).provider_label
