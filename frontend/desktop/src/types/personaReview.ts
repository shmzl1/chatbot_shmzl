import type { ChatTurnRecord, CharacterSummary } from "./chat";

export interface PersonaReviewSelectedTurn {
  turn_id?: string | number | null;
  session_id?: string | number | null;
  user_message: string;
  assistant_message: string;
  emotion?: string | null;
}

export interface PersonaReviewHistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface PersonaTurnFeedbackRequest {
  character_id: string;
  session_id?: string | null;
  turn_id?: number | null;
  user_message: string;
  assistant_message: string;
  rating: "good" | "bad" | "neutral";
  issue_tags: string[];
  comment: string;
}

export interface PersonaTurnFeedbackRecord extends PersonaTurnFeedbackRequest {
  id: number;
  created_at: string;
}

export interface PersonaFeedbackSummary {
  character_id: string;
  total_feedback: number;
  rating_counts: Record<string, number>;
  tag_counts: Record<string, number>;
  recent_feedback: PersonaTurnFeedbackRecord[];
}

export interface PersonaReviewChatRequest {
  selected_turns: PersonaReviewSelectedTurn[];
  message: string;
  history: PersonaReviewHistoryMessage[];
}

export interface PersonaReviewChatResponse {
  reply: string;
  history: PersonaReviewHistoryMessage[];
  suggested_tags: string[];
  should_generate_final: boolean;
  llm_profile?: string | null;
  model?: string | null;
}

export interface PersonaReviewFinalizeRequest {
  selected_turns: PersonaReviewSelectedTurn[];
  history: PersonaReviewHistoryMessage[];
  limit: number;
}

export interface PersonaReviewFinalizeResponse {
  main_issues: string[];
  revision_plan: string[];
  changed_fields: string[];
  patch: Record<string, unknown>;
  preview_character_json: Record<string, unknown>;
  risk_notes: string[];
  llm_profile?: string | null;
  model?: string | null;
  allowed_fields?: string[];
  protected_fields?: string[];
  feedback_stats?: PersonaFeedbackSummary;
  selected_turn_count?: number;
}

export interface PersonaReviewApplyRequest {
  preview_character_json: Record<string, unknown>;
  review_summary: Record<string, unknown>;
}

export interface PersonaReviewApplyResponse {
  status: string;
  character: CharacterSummary;
  changed_fields: string[];
  backup_path?: string;
}

export interface PersonaReviewRollbackResponse {
  status: string;
  character: CharacterSummary;
  restored_from: string;
}

export interface CharacterDetail extends Record<string, unknown> {
  id: string;
  display_name: string;
  avatar_url?: string | null;
}

export interface PersonaReviewTurn extends PersonaReviewSelectedTurn {
  id: number;
  character_id: string;
  created_at: string;
}

export function turnToPersonaReviewTurn(turn: ChatTurnRecord): PersonaReviewTurn {
  return {
    id: turn.id,
    turn_id: turn.id,
    session_id: turn.session_id,
    character_id: turn.character_id,
    user_message: turn.user_message,
    assistant_message: turn.reply,
    emotion: turn.emotion,
    created_at: turn.created_at,
  };
}
