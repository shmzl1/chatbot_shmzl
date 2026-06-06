from dataclasses import dataclass
from typing import Any, Dict, List

from core.config import settings
from core.schemas import CandidateReply, CharacterCard


CUSTOMER_SERVICE_MARKERS = (
    "很抱歉",
    "感谢您的",
    "请问您",
    "亲爱的用户",
    "如果您需要",
    "希望可以帮助",
    "祝您",
)

AI_MARKERS = (
    "我是ai",
    "我是 AI",
    "作为ai",
    "作为 AI",
    "语言模型",
    "人工智能",
    "扮演",
    "角色设定",
)

WARM_BUT_BLUNT_MARKERS = (
    "别",
    "行",
    "先",
    "少来",
    "听见了",
    "我在",
    "我陪",
    "别急",
    "别乱",
)


@dataclass(frozen=True)
class StyleJudgeResult:
    scores: List[Dict[str, Any]]
    best_index: int
    need_rewrite: bool


class StyleJudgeService:
    def judge(
        self,
        *,
        character: CharacterCard,
        candidates: List[CandidateReply],
    ) -> StyleJudgeResult:
        scores = [
            self._score_candidate(character=character, candidate=candidate, index=index)
            for index, candidate in enumerate(candidates)
        ]
        if not scores:
            return StyleJudgeResult(scores=[], best_index=0, need_rewrite=True)

        best = max(scores, key=lambda item: item["total"])
        return StyleJudgeResult(
            scores=scores,
            best_index=int(best["index"]),
            need_rewrite=float(best["total"]) < settings.style_score_threshold,
        )

    def _score_candidate(
        self,
        *,
        character: CharacterCard,
        candidate: CandidateReply,
        index: int,
    ) -> Dict[str, Any]:
        reply = candidate.reply.strip()
        problems: List[str] = []

        no_ai = not self._contains_any(reply, AI_MARKERS)
        no_customer_service = not self._contains_any(reply, CUSTOMER_SERVICE_MARKERS)
        if not no_ai:
            problems.append("暴露 AI 或角色扮演痕迹")
        if not no_customer_service:
            problems.append("客服感较重")

        length = len(reply)
        sentence_count = self._sentence_count(reply)
        has_blunt_marker = self._contains_any(reply, WARM_BUT_BLUNT_MARKERS)
        has_long_explanation = length > 120 or sentence_count > 5
        has_action_hint = self._contains_any(reply, ("先", "做", "说", "睡", "喝", "拿", "停", "看"))

        character_similarity = 7.0
        tone_consistency = 7.0
        naturalness = 8.0
        tts_suitability = 8.0
        lore_consistency = 8.0

        if has_blunt_marker:
            character_similarity += 1.0
            tone_consistency += 0.8
        if has_action_hint:
            character_similarity += 0.6
            naturalness += 0.4
        if length <= 80:
            tone_consistency += 0.7
            tts_suitability += 0.8
        if 8 <= length <= 90:
            naturalness += 0.4
        if has_long_explanation:
            tone_consistency -= 1.5
            tts_suitability -= 1.4
            problems.append("回复偏长或解释腔偏重")
        if not no_ai:
            character_similarity -= 3.0
            lore_consistency -= 2.0
        if not no_customer_service:
            tone_consistency -= 2.0
            naturalness -= 1.5
        if reply.endswith(("。", "？", "！")):
            tts_suitability += 0.2

        metrics = {
            "character_similarity": self._clamp(character_similarity),
            "lore_consistency": self._clamp(lore_consistency),
            "tone_consistency": self._clamp(tone_consistency),
            "naturalness": self._clamp(naturalness),
            "tts_suitability": self._clamp(tts_suitability),
        }
        total = sum(metrics.values()) / len(metrics)
        if no_ai:
            total += 0.2
        if no_customer_service:
            total += 0.2

        rewrite_advice = "；".join(problems)
        if not rewrite_advice and total < settings.style_score_threshold:
            rewrite_advice = "增强短句、嘴硬和具体行动感"

        return {
            "index": index,
            **metrics,
            "no_copy": True,
            "no_customer_service": no_customer_service,
            "no_ai_leak": no_ai,
            "total": round(self._clamp(total), 2),
            "problems": problems,
            "rewrite_advice": rewrite_advice,
        }

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        lowered = text.lower()
        return any(marker.lower() in lowered for marker in markers)

    def _sentence_count(self, text: str) -> int:
        return max(1, sum(text.count(mark) for mark in "。！？!?"))

    def _clamp(self, value: float) -> float:
        return max(0.0, min(10.0, value))


style_judge_service = StyleJudgeService()
