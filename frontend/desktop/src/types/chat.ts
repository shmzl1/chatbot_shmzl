export interface CharacterSummary {
  id: string;
  display_name: string;
  avatar_url?: string | null;
}

export interface CharacterListResponse {
  characters: CharacterSummary[];
}

export interface ChatTextRequest {
  character_id: string;
  message: string;
  session_id?: string | null;
  diary_entry_id?: number | null;
  debug_prompt?: boolean;
}

export interface CandidateReply {
  reply: string;
  emotion: string;
  reason: string;
}

export interface ChatTextResponse {
  session_id?: string | null;
  turn_id?: number | null;
  reply: string;
  emotion: string;
  candidates: CandidateReply[];
  audio_path?: string | null;
  style_score?: number | null;
  debug: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  emotion?: string;
}
