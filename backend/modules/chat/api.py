from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.config import settings
from core.schemas import (
    ChatRequest,
    ChatSessionArchiveResponse,
    ChatSessionListResponse,
    ChatSessionUpdateRequest,
    ChatTextRequest,
    ChatTextResponse,
    ChatTurnListResponse,
    UserRecord,
)
from modules.characters.service import character_service
from modules.diary.context import build_diary_context_for_chat
from modules.relationship_memory.service import relationship_memory_service
from services.auth_service import get_current_user
from services.database_service import database_service
from services.emotion_service import emotion_service
from services.llm_service import llm_service
from services.memory_suggestion_service import memory_suggestion_service
from services.prompt_builder import build_chat_prompt
from services.retrieval_service import retrieval_service
from services.rewrite_service import rewrite_service
from services.style_judge_service import style_judge_service
from services.tts_service import tts_service


router = APIRouter(tags=["chat"])


@router.get("/chat/sessions", response_model=ChatSessionListResponse)
def list_chat_sessions(
    query: Optional[str] = None,
    archived: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserRecord = Depends(get_current_user),
) -> ChatSessionListResponse:
    sessions, total = database_service.list_sessions(
        user_id=current_user.id,
        query=query,
        archived=archived,
        limit=limit,
        offset=offset,
    )
    return ChatSessionListResponse(sessions=sessions, total=total, limit=limit, offset=offset)


@router.get("/chat/sessions/{session_id}/turns", response_model=ChatTurnListResponse)
def list_chat_turns(
    session_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> ChatTurnListResponse:
    return ChatTurnListResponse(
        session_id=session_id,
        turns=database_service.list_turns(session_id, user_id=current_user.id),
    )


@router.patch("/chat/sessions/{session_id}", response_model=ChatSessionArchiveResponse)
def rename_chat_session(
    session_id: str,
    request: ChatSessionUpdateRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> ChatSessionArchiveResponse:
    return ChatSessionArchiveResponse(
        session=database_service.rename_chat_session(
            user_id=current_user.id,
            session_id=session_id,
            title=request.title,
        )
    )


@router.post("/chat/sessions/{session_id}/archive", response_model=ChatSessionArchiveResponse)
def archive_chat_session(
    session_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> ChatSessionArchiveResponse:
    return ChatSessionArchiveResponse(
        session=database_service.archive_chat_session(
            user_id=current_user.id,
            session_id=session_id,
        )
    )


@router.post("/chat/sessions/{session_id}/unarchive", response_model=ChatSessionArchiveResponse)
def unarchive_chat_session(
    session_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> ChatSessionArchiveResponse:
    return ChatSessionArchiveResponse(
        session=database_service.unarchive_chat_session(
            user_id=current_user.id,
            session_id=session_id,
        )
    )


@router.post("/chat/text", response_model=ChatTextResponse)
def chat_text(
    request: ChatTextRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> ChatTextResponse:
    return _run_chat(request=request, voice=False, current_user=current_user)


@router.post("/chat", response_model=ChatTextResponse)
def chat(
    request: ChatRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> ChatTextResponse:
    return _run_chat(request=request, voice=request.voice, current_user=current_user)


def _run_chat(request: ChatTextRequest, voice: bool, current_user: UserRecord) -> ChatTextResponse:
    character = character_service.get_character(request.character_id)
    if request.session_id:
        session = database_service.get_chat_session(user_id=current_user.id, session_id=request.session_id)
        if session.is_archived:
            raise HTTPException(status_code=409, detail="该对话已归档，请先恢复后再继续聊天。")
        if session.character_id != character.id:
            raise HTTPException(status_code=409, detail="该对话属于其他角色，不能继续写入。")
    retrieval_context = retrieval_service.retrieve(character.id, request.message)
    retrieval_context["lore"].extend(
        database_service.retrieve_knowledge(
            character_id=character.id,
            source_type="lore",
            query=request.message,
            limit=settings.top_k_lore,
        )
    )
    retrieval_context["dialogues"].extend(
        database_service.retrieve_knowledge(
            character_id=character.id,
            source_type="dialogue",
            query=request.message,
            limit=settings.top_k_dialogue,
        )
    )
    retrieval_context["reactions"].extend(
        database_service.retrieve_knowledge(
            character_id=character.id,
            source_type="reaction",
            query=request.message,
            limit=settings.top_k_reaction,
        )
    )
    history = database_service.recent_history(request.session_id, user_id=current_user.id, limit=10)
    memory_hits = database_service.retrieve_memories(
        character_id=character.id,
        query=request.message,
        limit=settings.top_k_memory,
    )
    relationship_memory_hits = relationship_memory_service.prompt_hits(
        character_id=character.id,
        limit=5,
    )
    retrieval_context["memories"] = memory_hits
    retrieval_context["relationship_memories"] = relationship_memory_hits
    retrieval_context["history"] = history
    diary_context = ""
    if request.diary_entry_id is not None:
        diary_context = build_diary_context_for_chat(
            user_id=current_user.id,
            entry_id=request.diary_entry_id,
        )
        retrieval_context["diary_context"] = diary_context
    prompt = build_chat_prompt(character, request.message, retrieval_context)
    generation = llm_service.generate_candidates(
        prompt,
        character,
        request.message,
        profile="chat",
    )
    judge_result = style_judge_service.judge(
        character=character,
        candidates=generation.candidates,
    )
    best = generation.candidates[judge_result.best_index]
    best_score = judge_result.scores[judge_result.best_index] if judge_result.scores else {}
    final_reply, rewritten = rewrite_service.rewrite_if_needed(
        character=character,
        user_message=request.message,
        reply=best.reply,
        score=best_score,
        need_rewrite=judge_result.need_rewrite,
    )
    final_emotion = emotion_service.select_emotion(
        character=character,
        user_message=request.message,
        candidate_emotion=best.emotion,
        reply=final_reply,
    )
    memory_suggestions = memory_suggestion_service.suggest(user_message=request.message)
    audio_path = None
    voice_reference_emotion = None
    if voice:
        _, public_url = tts_service.synthesize(
            character=character,
            text=final_reply,
            emotion=None,
        )
        audio_path = public_url
        voice_reference_emotion = "neutral"

    used_memory_ids = [
        hit["payload"]["id"]
        for hit in memory_hits
        if isinstance(hit.get("payload"), dict) and "id" in hit["payload"]
    ]
    database_service.mark_memories_used(used_memory_ids)
    relationship_memory_service.mark_prompt_hits_used(relationship_memory_hits)

    debug = {
        "character_id": character.id,
        "llm_profile": generation.profile,
        "mode": generation.provider,
        "model": generation.model,
        "voice": voice,
        "voice_reference_emotion": voice_reference_emotion,
        "audio_path": audio_path,
        **retrieval_service.used_ids(retrieval_context),
        "used_memories": [hit["id"] for hit in memory_hits],
        "used_relationship_memories": [hit["id"] for hit in relationship_memory_hits],
        "diary_entry_id": request.diary_entry_id,
        "diary_context_used": bool(diary_context),
        "history_count": len(history),
        "memory_suggestions": memory_suggestions,
        "style_judge": {
            "scores": judge_result.scores,
            "best_index": judge_result.best_index,
            "need_rewrite": judge_result.need_rewrite,
            "rewritten": rewritten,
        },
    }
    if settings.debug_prompt or request.debug_prompt:
        debug["prompt"] = prompt
        debug["raw_text"] = generation.raw_text

    session_id, turn_id = database_service.save_chat_turn(
        user_id=current_user.id,
        session_id=request.session_id,
        character_id=character.id,
        user_message=request.message,
        reply=final_reply,
        emotion=final_emotion,
        candidates=generation.candidates,
        debug=debug,
    )
    debug["session_id"] = session_id
    debug["turn_id"] = turn_id
    database_service.update_turn_debug(turn_id, debug)

    return ChatTextResponse(
        session_id=session_id,
        turn_id=turn_id,
        reply=final_reply,
        emotion=final_emotion,
        candidates=generation.candidates,
        audio_path=audio_path,
        style_score=best_score.get("total"),
        debug=debug,
    )
