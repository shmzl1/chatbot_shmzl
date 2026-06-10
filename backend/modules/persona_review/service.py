import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException
from pydantic import ValidationError

from core.schemas import CharacterCard, CharacterSummary
from modules.characters import pack_writer
from modules.characters.service import character_service
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
PATCH_ALLOWED_KEYS = {
    "style_contract",
    "speaking_style",
    "forbidden",
    "dialogues_append",
    "reactions_append",
    "bad_examples_append",
    "evaluation_criteria_append",
    "revision_note",
}
PATCH_PROTECTED_FIELDS = PROTECTED_FIELDS | {
    "gptsovits_base_url",
    "ref_audio_path",
    "prompt_text",
}
PATCH_APPEND_FIELD_MAP = {
    "dialogues_append": ("dialogues", "dialogue"),
    "reactions_append": ("reactions", "reaction"),
    "bad_examples_append": ("bad_examples", "bad_example"),
}
PATCH_CHANGED_FIELD_MAP = {
    "dialogues_append": "dialogues",
    "reactions_append": "reactions",
    "bad_examples_append": "bad_examples",
    "evaluation_criteria_append": "evaluation_criteria",
    "revision_note": "revision_notes",
}
MAX_FINALIZE_TURNS = 5
MAX_FINALIZE_HISTORY = 10
MAX_PATCH_ITEMS = 5


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
        llm_config = llm_service.runtime_config("persona_editor")
        response = llm_service.generate_json(
            prompt,
            (
                "你是人设编辑 AI，不是聊天角色本人。你只分析角色回复是否符合人设，"
                "和用户讨论怎么修改 character.json；你不能闲聊，不能假装自己是角色，"
                "只能分析、讨论、生成方案；未经用户确认不能写 character.json，"
                "不能声称已经写入文件。你必须只输出严格 JSON。"
            ),
            profile="persona_editor",
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
            "llm_profile": llm_config.profile,
            "model": llm_config.model,
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
        effective_limit = max(1, min(limit, 50))
        feedback_summary = database_service.persona_feedback_summary(
            character_id=character_id,
            limit=effective_limit,
        )
        normalized_turns = self._normalize_selected_turns(selected_turns)[:MAX_FINALIZE_TURNS]
        normalized_history = self._normalize_history(history)[-MAX_FINALIZE_HISTORY:]
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
        llm_config = llm_service.runtime_config("persona_editor")
        review = llm_service.generate_json(
            prompt,
            (
                "你是人设编辑 AI，不是聊天角色本人。你只分析、讨论、生成方案。"
                "你只能输出最终修改方案和 patch；未经用户确认不能写 character.json，"
                "不能声称已经写入文件。你必须只输出严格 JSON。"
            ),
            profile="persona_editor",
            strict_json=False,
        )
        current_payload = self._model_to_dict(character)
        review = self._normalize_finalize_patch_review(review)
        patch = review["patch"]
        preview = self._merge_persona_patch(
            current_payload=current_payload,
            patch=patch,
            review_summary=review,
        )
        self._validate_payload(
            character_id,
            preview,
            self._character_path(character_id),
            status_code=502,
        )
        changed_fields = [
            field_name
            for field_name in sorted(ALLOWED_REVIEW_FIELDS)
            if current_payload.get(field_name) != preview.get(field_name)
        ]
        review["preview_character_json"] = preview
        review["changed_fields"] = changed_fields
        review["patch"] = patch
        review["feedback_stats"] = feedback_summary
        review["selected_turn_count"] = len(normalized_turns)
        review["allowed_fields"] = sorted(ALLOWED_REVIEW_FIELDS)
        review["protected_fields"] = sorted(PROTECTED_FIELDS | {"gptsovits_base_url", "ref_audio_path", "prompt_text"})
        review["llm_profile"] = llm_config.profile
        review["model"] = llm_config.model
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
        llm_config = llm_service.runtime_config("persona_editor")
        review = llm_service.generate_json(
            prompt,
            (
                "你是人设编辑 AI，不是聊天角色本人。你只分析、讨论、生成方案。"
                "你必须只输出严格 JSON，且只能生成修改建议和预览；"
                "未经用户确认不能写 character.json，不得声称已经写入文件。"
            ),
            profile="persona_editor",
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
        review["llm_profile"] = llm_config.profile
        review["model"] = llm_config.model
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
        character_context = {
            "id": character_payload.get("id"),
            "display_name": character_payload.get("display_name"),
            "core_personality": character_payload.get("core_personality"),
            "speaking_style": character_payload.get("speaking_style"),
            "forbidden": character_payload.get("forbidden"),
            "style_contract": character_payload.get("style_contract"),
            "evaluation_criteria": character_payload.get("evaluation_criteria"),
            "bad_examples": self._list_preview(character_payload.get("bad_examples"), 5),
            "dialogues": self._list_preview(character_payload.get("dialogues"), 5),
            "reactions": self._list_preview(character_payload.get("reactions"), 5),
        }
        evidence_count = feedback_summary["total_feedback"] + len(selected_turns) + self._user_history_count(history)
        sample_policy = (
            "证据少于 5 条，只允许轻量修改 style_contract、bad_examples、evaluation_criteria、revision_notes。"
            if evidence_count < 5
            else "可以根据集中问题谨慎修改允许字段。"
        )
        return f"""请根据人设修改工作台的选中对话、用户评价、多轮编辑讨论、已保存反馈统计和当前角色摘要，生成最终修改 patch。

硬性规则：
- 只能输出 JSON 对象。
- 不要 Markdown。
- 不要 ```json 代码块。
- 不要解释文字。
- 不要注释。
- 字符串里的双引号必须转义。
- 数组和对象最后一项不能有尾逗号。
- 不要输出完整 character.json。
- 只输出 patch。
- patch 不能包含禁止字段。
- 不要修改 id、display_name、avatar_url、voice、gptsovits_base_url、ref_audio_path、prompt_text。
- 优先允许修改 style_contract、speaking_style、forbidden、dialogues、reactions、bad_examples、evaluation_criteria、revision_notes。
- 不要删除已有有效 dialogues，可以新增更符合人设的 dialogues。
- 可以新增 bad_examples，但不要把用户评价原文大量塞进 character.json。
- 不要生成非法 JSON。
- 不要声称已经写入文件。
- main_issues、revision_plan、risk_notes 最多各 5 条。
- changed_fields 只能写真实 character.json 字段，不能写 patch 字段名。
- changed_fields 正确示例：["dialogues", "bad_examples", "revision_notes"]。
- changed_fields 错误示例：["dialogues_append", "bad_examples_append", "revision_note"]。
- dialogues_append、reactions_append、bad_examples_append、evaluation_criteria_append 最多各 5 条。
- {sample_policy}

禁止字段：
{json.dumps(sorted(PATCH_PROTECTED_FIELDS), ensure_ascii=False, indent=2)}

当前角色摘要：
{json.dumps(character_context, ensure_ascii=False, indent=2)}

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
  "changed_fields": ["style_contract"],
  "patch": {{
    "style_contract": null,
    "speaking_style": null,
    "forbidden": null,
    "dialogues_append": [],
    "reactions_append": [],
    "bad_examples_append": [],
    "evaluation_criteria_append": [],
    "revision_note": null
  }},
  "risk_notes": ["风险提示"]
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
        self._assert_protected_fields_unchanged(current_payload, preview_character_json)
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
        self._validate_payload(character_id, merged, file_path)
        try:
            pack_writer.write_payload(character_id=character_id, payload=merged, backup=True)
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"Failed to apply persona review to {file_path}: {exc}",
            ) from exc

        character = character_service.get_character(character_id)
        backup_path = self._backup_path(character_id)
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
        try:
            backup_path = pack_writer.restore_previous_backup(character_id)
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"Failed to rollback persona file {self._character_path(character_id)}: {exc}",
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

    def _assert_protected_fields_unchanged(
        self,
        current_payload: Dict[str, Any],
        preview_payload: Dict[str, Any],
    ) -> None:
        changed = [
            field_name
            for field_name in sorted(PATCH_PROTECTED_FIELDS)
            if field_name in preview_payload and preview_payload.get(field_name) != current_payload.get(field_name)
        ]
        if changed:
            raise HTTPException(
                status_code=400,
                detail=f"Preview contains protected field changes: {', '.join(changed)}",
            )

    def _normalize_finalize_patch_review(self, review: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(review, dict):
            raise HTTPException(
                status_code=502,
                detail="Persona finalize response root must be a JSON object.",
            )

        patch = review.get("patch")
        if not isinstance(patch, dict):
            raise HTTPException(
                status_code=502,
                detail="Persona finalize JSON must include patch object.",
            )

        illegal_patch_keys = sorted(set(patch) - PATCH_ALLOWED_KEYS)
        protected_keys = sorted(set(patch) & PATCH_PROTECTED_FIELDS)
        if illegal_patch_keys or protected_keys:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Persona finalize patch contains unsupported or protected fields: "
                    f"{', '.join(illegal_patch_keys + protected_keys)}"
                ),
            )

        main_issues = self._string_list(review.get("main_issues"), "main_issues")
        revision_plan = self._string_list(review.get("revision_plan"), "revision_plan")
        risk_notes = self._string_list(review.get("risk_notes"), "risk_notes")
        changed_fields = self._changed_fields(review.get("changed_fields"))

        normalized_patch = {
            "style_contract": self._nullable_dict(patch.get("style_contract"), "patch.style_contract"),
            "speaking_style": self._nullable_string_list(
                patch.get("speaking_style"),
                "patch.speaking_style",
            ),
            "forbidden": self._nullable_string_list(
                patch.get("forbidden"),
                "patch.forbidden",
            ),
            "dialogues_append": self._object_list(
                patch.get("dialogues_append"),
                "patch.dialogues_append",
            ),
            "reactions_append": self._object_list(
                patch.get("reactions_append"),
                "patch.reactions_append",
            ),
            "bad_examples_append": self._object_list(
                patch.get("bad_examples_append"),
                "patch.bad_examples_append",
            ),
            "evaluation_criteria_append": self._string_list(
                patch.get("evaluation_criteria_append"),
                "patch.evaluation_criteria_append",
            ),
            "revision_note": self._nullable_dict(
                patch.get("revision_note"),
                "patch.revision_note",
            ),
        }

        return {
            "main_issues": main_issues,
            "revision_plan": revision_plan,
            "changed_fields": changed_fields,
            "patch": normalized_patch,
            "risk_notes": risk_notes,
        }

    def _merge_persona_patch(
        self,
        *,
        current_payload: Dict[str, Any],
        patch: Dict[str, Any],
        review_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged = json.loads(json.dumps(current_payload, ensure_ascii=False))

        if patch["style_contract"] is not None:
            merged["style_contract"] = patch["style_contract"]
        if patch["speaking_style"] is not None:
            merged["speaking_style"] = patch["speaking_style"]
        if patch["forbidden"] is not None:
            merged["forbidden"] = patch["forbidden"]

        for patch_field, (target_field, id_prefix) in PATCH_APPEND_FIELD_MAP.items():
            merged[target_field] = self._append_items_with_unique_ids(
                current_items=merged.get(target_field, []),
                append_items=patch[patch_field],
                id_prefix=id_prefix,
            )

        criteria = merged.get("evaluation_criteria")
        if not isinstance(criteria, list):
            criteria = []
        criteria.extend(patch["evaluation_criteria_append"])
        merged["evaluation_criteria"] = criteria

        notes = merged.get("revision_notes")
        if not isinstance(notes, list):
            notes = []
        if patch["revision_note"] is not None:
            note = dict(patch["revision_note"])
            note.setdefault("version", datetime.now(timezone.utc).date().isoformat())
            notes.append(note)
        elif self._patch_has_changes(patch):
            notes.append(
                {
                    "version": datetime.now(timezone.utc).date().isoformat(),
                    "reason": "根据用户确认的人设修改 patch 修正",
                    "changed_fields": review_summary.get("changed_fields", []),
                    "summary": self._review_summary_text(review_summary),
                }
            )
        merged["revision_notes"] = notes

        for field_name in PROTECTED_FIELDS:
            merged[field_name] = current_payload.get(field_name)

        return merged

    def _append_items_with_unique_ids(
        self,
        *,
        current_items: Any,
        append_items: List[Dict[str, Any]],
        id_prefix: str,
    ) -> List[Dict[str, Any]]:
        if not isinstance(current_items, list):
            current_items = []

        result = [item for item in current_items if isinstance(item, dict)]
        existing_ids = {str(item.get("id")) for item in result if item.get("id")}
        next_index = 1

        for item in append_items:
            new_item = dict(item)
            item_id = str(new_item.get("id") or "").strip()
            if not item_id or item_id in existing_ids:
                while True:
                    candidate = f"{id_prefix}_{next_index:03d}"
                    next_index += 1
                    if candidate not in existing_ids:
                        item_id = candidate
                        break
            new_item["id"] = item_id
            existing_ids.add(item_id)
            result.append(new_item)

        return result

    def _patch_has_changes(self, patch: Dict[str, Any]) -> bool:
        return any(
            [
                patch["style_contract"] is not None,
                patch["speaking_style"] is not None,
                patch["forbidden"] is not None,
                bool(patch["dialogues_append"]),
                bool(patch["reactions_append"]),
                bool(patch["bad_examples_append"]),
                bool(patch["evaluation_criteria_append"]),
            ]
        )

    def _review_summary_text(self, review_summary: Dict[str, Any]) -> str:
        main_issues = review_summary.get("main_issues")
        if isinstance(main_issues, list) and main_issues:
            return "；".join(str(item) for item in main_issues[:3])
        return "根据人设编辑 patch 调整角色表达规则"

    def _string_list(self, value: Any, field_name: str) -> List[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise HTTPException(
                status_code=502,
                detail=f"Persona finalize field '{field_name}' must be an array.",
            )
        return [str(item).strip() for item in value[:MAX_PATCH_ITEMS] if str(item).strip()]

    def _nullable_string_list(self, value: Any, field_name: str) -> List[str] | None:
        if value is None:
            return None
        return self._string_list(value, field_name)

    def _object_list(self, value: Any, field_name: str) -> List[Dict[str, Any]]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise HTTPException(
                status_code=502,
                detail=f"Persona finalize field '{field_name}' must be an array.",
            )
        result = []
        for item in value[:MAX_PATCH_ITEMS]:
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=502,
                    detail=f"Persona finalize field '{field_name}' items must be objects.",
                )
            protected_keys = sorted(set(item) & PATCH_PROTECTED_FIELDS)
            if protected_keys:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        f"Persona finalize field '{field_name}' item contains protected fields: "
                        f"{', '.join(protected_keys)}"
                    ),
                )
            result.append(dict(item))
        return result

    def _nullable_dict(self, value: Any, field_name: str) -> Dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise HTTPException(
                status_code=502,
                detail=f"Persona finalize field '{field_name}' must be an object or null.",
            )
        protected_keys = sorted(set(value) & PATCH_PROTECTED_FIELDS)
        if protected_keys:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"Persona finalize field '{field_name}' contains protected fields: "
                    f"{', '.join(protected_keys)}"
                ),
            )
        return dict(value)

    def _changed_fields(self, value: Any) -> List[str]:
        raw_fields = self._string_list(value, "changed_fields")
        fields: List[str] = []
        invalid: List[str] = []
        for field in raw_fields:
            normalized = PATCH_CHANGED_FIELD_MAP.get(field, field)
            if normalized in ALLOWED_REVIEW_FIELDS:
                if normalized not in fields:
                    fields.append(normalized)
            else:
                invalid.append(field)

        if invalid:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Persona finalize changed_fields contains unsupported fields: "
                    f"{', '.join(sorted(set(invalid)))}"
                ),
            )
        return fields

    def _list_preview(self, value: Any, limit: int) -> List[Any]:
        if not isinstance(value, list):
            return []
        return value[:limit]

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
                    "emotion": item.get("emotion"),
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

    def _validate_payload(
        self,
        character_id: str,
        payload: Dict[str, Any],
        file_path: Path,
        status_code: int = 500,
    ) -> None:
        errors: List[str] = []
        character_service.validate_payload(
            payload=payload,
            file_path=file_path,
            expected_id=character_id,
            errors=errors,
        )
        if errors:
            raise HTTPException(
                status_code=status_code,
                detail=f"Character preview '{file_path}' is invalid: {'; '.join(errors)}",
            )
        try:
            CharacterCard(**payload)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status_code,
                detail=f"Character preview '{file_path}' schema is invalid: {exc}",
            ) from exc

    def _character_path(self, character_id: str) -> Path:
        return character_service.character_path(character_id)

    def _backup_path(self, character_id: str) -> Path:
        return character_service.backup_path(character_id)

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
