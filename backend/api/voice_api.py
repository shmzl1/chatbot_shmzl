from fastapi import APIRouter

from core.schemas import VoiceTestRequest, VoiceTestResponse
from services.character_service import character_service
from services.emotion_service import emotion_service
from services.tts_service import tts_service


router = APIRouter(tags=["voice"])


@router.post("/voice/test", response_model=VoiceTestResponse)
def voice_test(request: VoiceTestRequest) -> VoiceTestResponse:
    character = character_service.get_character(request.character_id)
    emotion = emotion_service.select_emotion(
        character=character,
        user_message="",
        candidate_emotion=request.emotion,
        reply=request.text,
    )
    audio_path, public_url = tts_service.synthesize(
        character=character,
        text=request.text,
        emotion=emotion,
    )
    return VoiceTestResponse(
        audio_path=audio_path,
        public_url=public_url,
        emotion=emotion,
    )
