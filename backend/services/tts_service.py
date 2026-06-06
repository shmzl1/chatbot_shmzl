from datetime import datetime, timezone
from pathlib import Path

import requests
from fastapi import HTTPException

from core.config import settings
from core.schemas import CharacterCard


class TTSService:
    def synthesize(
        self,
        *,
        character: CharacterCard,
        text: str,
        emotion: str,
    ) -> tuple[str, str]:
        ref_audio_path, prompt_text = self._select_reference(character.id, emotion)
        output_dir = settings.outputs_dir / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = self._filename(character.id, emotion)
        output_path = output_dir / filename

        payload = {
            "text": text,
            "text_lang": character.voice.language,
            "ref_audio_path": str(ref_audio_path),
            "prompt_text": prompt_text,
            "prompt_lang": character.voice.language,
            "text_split_method": "cut5",
            "batch_size": 1,
            "media_type": "wav",
            "streaming_mode": False,
            "top_k": 15,
            "top_p": 1,
            "temperature": 0.8,
            "speed_factor": character.voice.speed_factor,
        }

        try:
            response = requests.post(
                f"{settings.gptsovits_base_url}/tts",
                json=payload,
                timeout=settings.gptsovits_timeout_seconds,
            )
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=503,
                detail=f"GPT-SoVITS request failed: {exc}",
            ) from exc

        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"GPT-SoVITS returned {response.status_code}: {response.text[:500]}",
            )

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            data = response.json()
            remote_path = data.get("audio_path") or data.get("path")
            if remote_path:
                return str(remote_path), self._public_url_from_path(remote_path)
            raise HTTPException(
                status_code=502,
                detail="GPT-SoVITS returned JSON without audio_path.",
            )

        output_path.write_bytes(response.content)
        relative_path = f"outputs/audio/{filename}"
        return relative_path, f"/outputs/audio/{filename}"

    def _select_reference(self, character_id: str, emotion: str) -> tuple[Path, str]:
        emotion_dir = settings.data_dir / "voice_refs" / character_id / emotion
        fallback_dir = settings.data_dir / "voice_refs" / character_id / "neutral"

        ref_audio_path = emotion_dir / "ref_001.wav"
        ref_text_path = emotion_dir / "ref_001.txt"
        if not ref_audio_path.exists() and emotion != "neutral":
            ref_audio_path = fallback_dir / "ref_001.wav"
            ref_text_path = fallback_dir / "ref_001.txt"

        if not ref_audio_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Missing reference audio: {ref_audio_path}",
            )

        prompt_text = ""
        if ref_text_path.exists():
            prompt_text = ref_text_path.read_text(encoding="utf-8").strip()

        return ref_audio_path, prompt_text

    def _filename(self, character_id: str, emotion: str) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        return f"{character_id}_{emotion}_{stamp}.wav"

    def _public_url_from_path(self, path: str) -> str:
        normalized = path.replace("\\", "/")
        if normalized.startswith("outputs/"):
            return f"/{normalized}"
        return normalized


tts_service = TTSService()
