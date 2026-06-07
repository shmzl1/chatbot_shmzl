import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException
from pydantic import ValidationError

from core.config import settings
from core.schemas import CharacterCard, CharacterSummary
from services.character_service import CHARACTER_FILE, character_service
from services.database_service import database_service
from services.llm_service import llm_service


ALLOWED_REVIEW_FIELDS = {
    "style_contract",
    "speaking_style",
    "forbidden",
    "dialogues",
    "reactions",
    "bad_examples",
    "evaluation_criteria",
    "revision_notes",
}
LIGHTWEIGHT_REVIEW_FIELDS = {
    "style_contract",
    "bad_examples",
    "evaluation_criteria",
    "revision_notes",
}
PROTECTED_FIELDS = {
    "id",
    "display_name",
    "avatar_url",
    "voice",
}


class PersonaReviewService:
    def chat(
        self,
        *,
        character_id: str,
        selected_turns: List[Any],
        message: str,
        history: List[Any],
    ) -> Dict[str, Any]:
        character = character_service.get_character(character_id)
        feedback_summary = database_service.persona_feedback_summary(
            character_id=character_id,
            limit=30,
        )
        normalized_turns = self._normalize_selected_turns(selected_turns)
        normalized_history = self._normalize_history(history)
        prompt = self._build_chat_prompt(
            character=character,
            selected_turns=normalized_turns,
            message=message,
            history=normalized_history,
            feedback_summary=feedback_summary,
        )
        response = llm_service.generate_json(
            prompt,
            (
                "你是人设编辑 AI，不是聊天角色本人。你只分析角色回复是否符合人设，"
                "和用户讨论怎么修改 character.json；你不能闲聊，不能假装自己是角色，"
                "不能声称已经写入文件。你必须只输出严格 JSON。"
            ),
        )
        reply = str(response.get("reply", "")).strip()
        if not reply:
            raise HTTPException(
                status_code=502,
                detail="Persona editor chat response must include non-empty reply.",
            )
        suggested_tags = response.get("suggested_tags", [])
        if not isinstance(suggested_tags, list):
            suggested_tags = []
        updated_history = normalized_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply},
        ]
        return {
            "reply": reply,
            "history": updated_history,
            "suggested_tags": [str(tag) for tag in suggested_tags[:12]],
            "should_generate_final": bool(response.get("should_generate_final", False)),
        }

    def finalize(
        self,
        *,
        character_id: str,
        selected_turns: List[Any],
        history: List[Any],
        limit: int,
    ) -> Dict[str, Any]:
        character = character_service.get_character(character_id)
        feedback_summary = database_service.persona_feedback_summary(
            character_id=character_id,
            limit=limit,
        )
        normalized_turns = self._normalize_selected_turns(selected_turns)
        normalized_history = self._normalize_history(history)
        if not normalized_turns and not normalized_history and feedback_summary["total_feedback"] == 0:
            raise HTTPException(
                status_code=400,
                detail="No selected turns, editor history, or persona feedback available for finalization.",
            )

        prompt = self._build_finalize_prompt(
            character=character,
            selected_turns=normalized_turns,
            history=normalized_history,
            feedback_summary=feedback_summary,
        )
        review = llm_service.generate_json(
            prompt,
            (
                "你是人设编辑 AI。你只能输出最终修改方案和 preview_character_json，"
                "不能声称已经写入文件。你必须只输出严格 JSON。"
            ),
        )
        preview = review.get("preview_character_json")
        if not isinstance(preview, dict):
            raise HTTPException(
                status_code=502,
                detail="Persona finalize JSON must include preview_character_json object.",
            )
        current_payload = self._model_to_dict(character)
        evidence_count = feedback_summary["total_feedback"] + len(normalized_turns) + self._user_history_count(normalized_history)
        preview = self._sanitize_preview(
            current_payload=current_payload,
            preview_payload=preview,
            feedback_count=evidence_count,
            review_summary=review,
        )
        self._validate_payload(character_id, preview, self._character_path(character_id))
        changed_fields = [
            field_name
            for field_name in sorted(ALLOWED_REVIEW_FIELDS)
            if current_payload.get(field_name) != preview.get(field_name)
        ]
        review["preview_character_json"] = preview
        review["changed_fields"] = changed_fields
        review["feedback_stats"] = feedback_summary
        review["selected_turn_count"] = len(normalized_turns)
        review["allowed_fields"] = sorted(ALLOWED_REVIEW_FIELDS)
        review["protected_fields"] = sorted(PROTECTED_FIELDS | {"gptsovits_base_url", "ref_audio_path", "prompt_text"})
        return review

    def summarize(self, character_id: str, limit: int) -> Dict[str, Any]:
        character = character_service.get_character(character_id)
        feedback_summary = database_service.persona_feedback_summary(
            character_id=character_id,
            limit=limit,
        )
        recent_feedback = feedback_summary["recent_feedback"]
        if not recent_feedback:
            raise HTTPException(
                status_code=400,
                detail=f"No persona feedback found for character '{character_id}'.",
            )

        prompt = self._build_summary_prompt(character, feedback_summary)
        review = llm_service.generate_json(
            prompt,
            "你是角色人设编辑器。你必须只输出严格 JSON，且只能生成修改建议和预览，不得声称已经写入文件。",
        )
        preview = review.get("preview_character_json")
        if not isinstance(preview, dict):
            raise HTTPException(
                status_code=502,
                detail="Persona review JSON must include preview_character_json object.",
            )

        current_payload = self._model_to_dict(character)
        preview = self._sanitize_preview(
            current_payload=current_payload,
            preview_payload=preview,
            feedback_count=feedback_summary["total_feedback"],
            review_summary=review,
        )
        self._validate_payload(character_id, preview, self._character_path(character_id))
        review["preview_character_json"] = preview
        review["feedback_stats"] = feedback_summary
        review["sample_policy"] = (
            "lightweight" if feedback_summary["total_feedback"] < 5 else "normal"
        )
        review["allowed_fields"] = sorted(ALLOWED_REVIEW_FIELDS)
        review["protected_fields"] = sorted(PROTECTED_FIELDS | {"gptsovits_base_url", "ref_audio_path", "prompt_text"})
        return review

    def _build_chat_prompt(
        self,
        *,
        character: CharacterCard,
        selected_turns: List[Dict[str, Any]],
        message: str,
        history: List[Dict[str, str]],
        feedback_summary: Dict[str, Any],
    ) -> str:
        character_payload = self._model_to_dict(character)
        editor_context = {
            "id": character_payload.get("id"),
            "display_name": character_payload.get("display_name"),
            "core_personality": character_payload.get("core_personality"),
            "speaking_style": character_payload.get("speaking_style"),
            "forbidden": character_payload.get("forbidden"),
            "style_contract": character_payload.get("style_contract"),
            "evaluation_criteria": character_payload.get("evaluation_criteria"),
            "bad_examples": character_payload.get("bad_examples"),
        }
        return f"""你正在和用户进行“人设修改工作台”的多轮讨论。你不是角色本人，而是人设编辑 AI。

任务：
- 分析选中的角色回复哪里符合或不符合人设。
- 帮用户把零散评价整理成可修改 character.json 的方向。
- 不要输出 preview_character_json。
- 不要声称已经修改文件。
- 如果信息足够生成最终方案，should_generate_final 可以为 true。

当前角色编辑上下文：
{json.dumps(editor_context, ensure_ascii=False, indent=2)}

已保存反馈统计：
{json.dumps(feedback_summary, ensure_ascii=False, indent=2)}

选中的对话：
{json.dumps(selected_turns, ensure_ascii=False, indent=2)}

已有编辑对话历史：
{json.dumps(history, ensure_ascii=False, indent=2)}

用户这轮评价：
{message}

输出 JSON：
{{
  "reply": "给用户的人设编辑回复，简洁说明你看到了什么、建议怎么改、还需要用户补充什么",
  "suggested_tags": ["too_ai", "out_of_character"],
  "should_generate_final": false
}}
"""

    def _build_finalize_prompt(
        self,
        *,
        character: CharacterCard,
        selected_turns: List[Dict[str, Any]],
        history: List[Dict[str, str]],
        feedback_summary: Dict[str, Any],
    ) -> str:
        character_payload = self._model_to_dict(character)
        editable_snapshot = {
            key: character_payload.get(key)
            for key in sorted(ALLOWED_REVIEW_FIELDS)
            if key in character_payload
        }
        evidence_count = feedback_summary["total_feedback"] + len(selected_turns) + self._user_history_count(history)
        sample_policy = (
            "证据少于 5 条，只允许轻量修改 style_contract、bad_examples、evaluation_criteria、revision_notes。"
            if evidence_count < 5
            else "可以根据集中问题谨慎修改允许字段。"
        )
        return f"""请根据人设修改工作台的选中对话、用户评价、多轮编辑讨论、已保存反馈统计和当前 character.json，生成最终修改方案。

硬性规则：
- 只输出 JSON。
- 不要修改 id、display_name、avatar_url、voice、gptsovits_base_url、ref_audio_path、prompt_text。
- 优先允许修改 style_contract、speaking_style、forbidden、dialogues、reactions、bad_examples、evaluation_criteria、revision_notes。
- 不要删除已有有效 dialogues，可以新增更符合人设的 dialogues。
- 可以新增 bad_examples，但不要把用户评价原文大量塞进 character.json。
- 不要生成非法 JSON。
- 不要声称已经写入文件。
- {sample_policy}

当前完整 character.json：
{json.dumps(character_payload, ensure_ascii=False, indent=2)}

当前可编辑字段快照：
{json.dumps(editable_snapshot, ensure_ascii=False, indent=2)}

选中的对话：
{json.dumps(selected_turns, ensure_ascii=False, indent=2)}

人设编辑对话历史：
{json.dumps(history, ensure_ascii=False, indent=2)}

已保存反馈统计：
{json.dumps(feedback_summary, ensure_ascii=False, indent=2)}

输出 JSON：
{{
  "main_issues": ["当前角色主要问题"],
  "revision_plan": ["具体修改计划"],
  "changed_fields": ["预计修改字段"],
  "risk_notes": ["风险提示"],
  "preview_character_json": {{完整 character.json 对象}}
}}
"""

    def apply(
        self,
        *,
        character_id: str,
        preview_character_json: Dict[str, Any],
        review_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        current = character_service.get_character(character_id)
        current_payload = self._model_to_dict(current)
        merged = self._sanitize_preview(
            current_payload=current_payload,
            preview_payload=preview_character_json,
            feedback_count=None,
            review_summary=review_summary,
        )
        changed_fields = [
            field_name
            for field_name in sorted(ALLOWED_REVIEW_FIELDS)
            if current_payload.get(field_name) != merged.get(field_name)
        ]
        if not changed_fields:
            raise HTTPException(
                status_code=400,
                detail="No allowed character fields changed in preview_character_json.",
            )

        file_path = self._character_path(character_id)
        backup_path = self._backup_path(character_id)
        temp_path = file_path.with_suffix(".apply.tmp.json")

        self._validate_payload(character_id, merged, file_path)
        try:
            temp_path.write_text(
                json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._validate_payload(character_id, self._read_json(temp_path), temp_path)

            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            os.replace(temp_path, file_path)
        except Exception as exc:
            if temp_path.exists():
                temp_path.unlink()
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"Failed to apply persona review to {file_path}: {exc}",
            ) from exc

        character = character_service.get_character(character_id)
        return {
            "status": "ok",
            "character": CharacterSummary(
                id=character.id,
                display_name=character.display_name,
                avatar_url=character.avatar_url,
            ).dict(),
            "character_path": str(file_path),
            "backup_path": str(backup_path),
            "changed_fields": changed_fields,
        }

    def rollback(self, character_id: str) -> Dict[str, Any]:
        backup_path = self._backup_path(character_id)
        file_path = self._character_path(character_id)
        temp_path = file_path.with_suffix(".rollback.tmp.json")
        if not backup_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Previous character backup does not exist: {backup_path}",
            )

        payload = self._read_json(backup_path)
        self._validate_payload(character_id, payload, file_path)
        try:
            temp_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._validate_payload(character_id, self._read_json(temp_path), temp_path)
            os.replace(temp_path, file_path)
        except Exception as exc:
            if temp_path.exists():
                temp_path.unlink()
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"Failed to rollback persona file {file_path}: {exc}",
            ) from exc

        character = character_service.get_character(character_id)
        return {
            "status": "ok",
            "character": CharacterSummary(
                id=character.id,
                display_name=character.display_name,
                avatar_url=character.avatar_url,
            ).dict(),
            "restored_from": str(backup_path),
        }

    def debug(self, character_id: str) -> Dict[str, Any]:
        validation = character_service.validate_pack(character_id)
        file_path = self._character_path(character_id)
        backup_path = self._backup_path(character_id)
        result = dict(validation)
        result.update(
            {
                "style_contract_exists": False,
                "evaluation_criteria_exists": False,
                "bad_examples_count": 0,
                "revision_notes_count": 0,
                "persona_feedback_count": 0,
                "recent_issue_tag_counts": {},
                "previous_backup_exists": backup_path.exists(),
                "previous_backup_path": str(backup_path),
                "last_revision_note": None,
            }
        )
        if validation["errors"]:
            return result

        payload = self._read_json(file_path)
        style_contract = payload.get("style_contract")
        evaluation_criteria = payload.get("evaluation_criteria")
        bad_examples = payload.get("bad_examples")
        revision_notes = payload.get("revision_notes")
        feedback_summary = database_service.persona_feedback_summary(
            character_id=character_id,
            limit=30,
        )
        result.update(
            {
                "style_contract_exists": isinstance(style_contract, dict),
                "evaluation_criteria_exists": isinstance(evaluation_criteria, list),
                "bad_examples_count": len(bad_examples) if isinstance(bad_examples, list) else 0,
                "revision_notes_count": len(revision_notes) if isinstance(revision_notes, list) else 0,
                "persona_feedback_count": feedback_summary["total_feedback"],
                "recent_issue_tag_counts": feedback_summary["issue_tag_counts"],
                "last_revision_note": (
                    revision_notes[-1]
                    if isinstance(revision_notes, list) and revision_notes
                    else None
                ),
            }
        )
        return result

    def _build_summary_prompt(
        self,
        character: CharacterCard,
        feedback_summary: Dict[str, Any],
    ) -> str:
        character_payload = self._model_to_dict(character)
        editable_snapshot = {
            key: character_payload.get(key)
            for key in sorted(ALLOWED_REVIEW_FIELDS)
            if key in character_payload
        }
        sample_policy = (
            "反馈少于 5 条，只允许轻量建议，不要大改。"
            if feedback_summary["total_feedback"] < 5
            else "可以根据集中问题谨慎提出结构化修改。"
        )
        return f"""请根据用户对角色回复的人设反馈，生成角色人设修改建议和修改后的 character.json 预览。

硬性规则：
- 只输出 JSON。
- 不要修改 id、display_name、avatar_url、voice、gptsovits_base_url、ref_audio_path、prompt_text。
- 优先修改 style_contract、speaking_style、forbidden、dialogues、reactions、bad_examples、evaluation_criteria、revision_notes。
- 不要删除已有有效 dialogues；必要时只优化或新增。
- 不要把反馈原文大量塞进人设。
- {sample_policy}

角色完整 JSON：
{json.dumps(character_payload, ensure_ascii=False, indent=2)}

当前可编辑字段快照：
{json.dumps(editable_snapshot, ensure_ascii=False, indent=2)}

反馈统计和最近反馈：
{json.dumps(feedback_summary, ensure_ascii=False, indent=2)}

输出 JSON 格式：
{{
  "main_issues": ["当前角色主要问题"],
  "too_ai_expressions": ["哪些表达太 AI"],
  "out_of_character": ["哪些表达不符合人设"],
  "strengthen_styles": ["哪些风格应该加强"],
  "remove_styles": ["哪些风格应该删除或弱化"],
  "suggested_fields": ["建议修改的字段名"],
  "suggested_dialogues": [{{"id": "dialogue_xxx", "scene": "...", "style_summary": "...", "rewrite_rule": "..."}}],
  "suggested_reactions": [{{"id": "reaction_xxx", "situation": "...", "reaction": "...", "reply_pattern": "...", "avoid": ["..."]}}],
  "risk_notes": ["修改风险提示"],
  "preview_character_json": {{完整 character.json 对象}}
}}
"""

    def _sanitize_preview(
        self,
        *,
        current_payload: Dict[str, Any],
        preview_payload: Dict[str, Any],
        feedback_count: int | None,
        review_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged = dict(current_payload)
        allowed_fields = (
            LIGHTWEIGHT_REVIEW_FIELDS
            if feedback_count is not None and feedback_count < 5
            else ALLOWED_REVIEW_FIELDS
        )
        for field_name in allowed_fields:
            if field_name in preview_payload:
                merged[field_name] = preview_payload[field_name]

        for field_name in PROTECTED_FIELDS:
            merged[field_name] = current_payload.get(field_name)

        merged["dialogues"] = self._preserve_existing_items(
            current_payload.get("dialogues", []),
            merged.get("dialogues", []),
        )
        merged["reactions"] = self._preserve_existing_items(
            current_payload.get("reactions", []),
            merged.get("reactions", []),
        )
        merged["revision_notes"] = self._revision_notes(
            current_payload=current_payload,
            merged_payload=merged,
            feedback_count=feedback_count,
            review_summary=review_summary,
        )
        return merged

    def _revision_notes(
        self,
        *,
        current_payload: Dict[str, Any],
        merged_payload: Dict[str, Any],
        feedback_count: int | None,
        review_summary: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        notes = merged_payload.get("revision_notes")
        if not isinstance(notes, list):
            notes = list(current_payload.get("revision_notes") or [])
        changed_fields = [
            field_name
            for field_name in sorted(ALLOWED_REVIEW_FIELDS - {"revision_notes"})
            if current_payload.get(field_name) != merged_payload.get(field_name)
        ]
        summary = review_summary.get("summary")
        if not summary:
            main_issues = review_summary.get("main_issues")
            summary = "；".join(str(item) for item in main_issues[:3]) if isinstance(main_issues, list) else ""
        notes.append(
            {
                "version": datetime.now(timezone.utc).date().isoformat(),
                "reason": (
                    f"根据最近 {feedback_count} 条用户反馈修正"
                    if feedback_count is not None
                    else "根据用户确认的人设修改建议修正"
                ),
                "changed_fields": changed_fields,
                "summary": summary or "根据人设反馈调整角色表达规则",
            }
        )
        return notes

    def _preserve_existing_items(
        self,
        current_items: Any,
        preview_items: Any,
    ) -> List[Dict[str, Any]]:
        if not isinstance(current_items, list):
            current_items = []
        if not isinstance(preview_items, list):
            preview_items = []
        result = [item for item in preview_items if isinstance(item, dict)]
        seen = {str(item.get("id")) for item in result if item.get("id")}
        for item in current_items:
            if isinstance(item, dict) and item.get("id") and str(item["id"]) not in seen:
                result.append(item)
                seen.add(str(item["id"]))
        return result

    def _normalize_selected_turns(self, selected_turns: List[Any]) -> List[Dict[str, Any]]:
        normalized = []
        for item in selected_turns[:20]:
            if hasattr(item, "model_dump"):
                item = item.model_dump()
            elif hasattr(item, "dict"):
                item = item.dict()
            if not isinstance(item, dict):
                continue
            user_message = str(item.get("user_message", "")).strip()
            assistant_message = str(item.get("assistant_message", "")).strip()
            if not user_message or not assistant_message:
                continue
            normalized.append(
                {
                    "turn_id": item.get("turn_id"),
                    "session_id": item.get("session_id"),
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                }
            )
        return normalized

    def _normalize_history(self, history: List[Any]) -> List[Dict[str, str]]:
        normalized = []
        for item in history[-40:]:
            if hasattr(item, "model_dump"):
                item = item.model_dump()
            elif hasattr(item, "dict"):
                item = item.dict()
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "")).strip()
            content = str(item.get("content", "")).strip()
            if role not in {"user", "assistant"} or not content:
                continue
            normalized.append({"role": role, "content": content})
        return normalized

    def _user_history_count(self, history: List[Dict[str, str]]) -> int:
        return len([item for item in history if item.get("role") == "user"])

    def _validate_payload(self, character_id: str, payload: Dict[str, Any], file_path: Path) -> None:
        errors: List[str] = []
        character_service._validate_payload(
            payload=payload,
            file_path=file_path,
            expected_id=character_id,
            errors=errors,
        )
        if errors:
            raise HTTPException(
                status_code=500,
                detail=f"Character preview '{file_path}' is invalid: {'; '.join(errors)}",
            )
        try:
            CharacterCard(**payload)
        except ValidationError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Character preview '{file_path}' schema is invalid: {exc}",
            ) from exc

    def _character_path(self, character_id: str) -> Path:
        return settings.data_dir / "character_packs" / character_id / CHARACTER_FILE

    def _backup_path(self, character_id: str) -> Path:
        return settings.data_dir / "character_packs" / character_id / "backups" / "character.previous.json"

    def _read_json(self, file_path: Path) -> Dict[str, Any]:
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Character JSON is invalid at {file_path}: {exc}",
            ) from exc
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=500,
                detail=f"Character JSON root must be an object: {file_path}",
            )
        return payload

    def _model_to_dict(self, character: CharacterCard) -> Dict[str, Any]:
        if hasattr(character, "model_dump"):
            return character.model_dump()
        return character.dict()


persona_review_service = PersonaReviewService()
