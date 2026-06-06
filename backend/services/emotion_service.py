from core.schemas import CharacterCard


ALLOWED_EMOTIONS = {"neutral", "soft", "angry", "tired", "teasing", "serious"}


class EmotionService:
    def select_emotion(
        self,
        *,
        character: CharacterCard,
        user_message: str,
        candidate_emotion: str,
        reply: str,
    ) -> str:
        if candidate_emotion in ALLOWED_EMOTIONS:
            base = candidate_emotion
        else:
            base = character.voice.default_emotion

        text = f"{user_message} {reply}"
        if any(word in text for word in ("累", "睡不着", "困", "撑不住")):
            return "tired"
        if any(word in text for word in ("生气", "烦", "讨厌", "滚")):
            return "angry"
        if any(word in text for word in ("没用", "难受", "考砸", "失败", "想哭")):
            return "soft"
        if any(word in text for word in ("开玩笑", "逗", "夸", "喜欢")):
            return "teasing"
        if any(word in text for word in ("认真", "重要", "必须", "放弃")):
            return "serious"
        return base


emotion_service = EmotionService()
