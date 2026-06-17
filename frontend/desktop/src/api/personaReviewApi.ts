import { requestJson } from "./client";
import type {
  CharacterDetail,
  PersonaFeedbackSummary,
  PersonaReviewApplyRequest,
  PersonaReviewApplyResponse,
  PersonaReviewChatRequest,
  PersonaReviewChatResponse,
  PersonaReviewFinalizeRequest,
  PersonaReviewFinalizeResponse,
  PersonaReviewRollbackResponse,
  PersonaTurnFeedbackRecord,
  PersonaTurnFeedbackRequest,
} from "../types/personaReview";

export function savePersonaTurnFeedback(request: PersonaTurnFeedbackRequest): Promise<PersonaTurnFeedbackRecord> {
  return requestJson<PersonaTurnFeedbackRecord>("/feedback/persona/turn", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function getPersonaFeedbackSummary(characterId: string, limit = 30): Promise<PersonaFeedbackSummary> {
  return requestJson<PersonaFeedbackSummary>(`/feedback/persona/${encodeURIComponent(characterId)}?limit=${limit}`);
}

export function getCharacterDetail(characterId: string): Promise<CharacterDetail> {
  return requestJson<CharacterDetail>(`/characters/${encodeURIComponent(characterId)}`);
}

export function chatPersonaReview(
  characterId: string,
  request: PersonaReviewChatRequest,
): Promise<PersonaReviewChatResponse> {
  return requestJson<PersonaReviewChatResponse>(`/characters/${encodeURIComponent(characterId)}/persona-review/chat`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function finalizePersonaReview(
  characterId: string,
  request: PersonaReviewFinalizeRequest,
): Promise<PersonaReviewFinalizeResponse> {
  return requestJson<PersonaReviewFinalizeResponse>(`/characters/${encodeURIComponent(characterId)}/persona-review/finalize`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function applyPersonaReview(
  characterId: string,
  request: PersonaReviewApplyRequest,
): Promise<PersonaReviewApplyResponse> {
  return requestJson<PersonaReviewApplyResponse>(`/characters/${encodeURIComponent(characterId)}/persona-review/apply`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function rollbackPersonaReview(characterId: string): Promise<PersonaReviewRollbackResponse> {
  return requestJson<PersonaReviewRollbackResponse>(`/characters/${encodeURIComponent(characterId)}/persona-review/rollback`, {
    method: "POST",
  });
}
