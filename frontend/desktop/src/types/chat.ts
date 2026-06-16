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

export interface ChatSessionSummary {
  id: string;
  character_id: string;
  user_id?: number | null;
  title: string;
  is_archived: boolean;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
  turn_count: number;
  last_user_message?: string | null;
  last_reply?: string | null;
}

export interface ChatSessionListResponse {
  sessions: ChatSessionSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ChatSessionUpdateRequest {
  title: string;
}

export interface ChatSessionSearchParams {
  query?: string;
  archived?: boolean;
  limit?: number;
  offset?: number;
}

export interface ChatSessionArchiveResponse {
  session: ChatSessionSummary;
}

export interface ChatTurnRecord {
  id: number;
  session_id: string;
  character_id: string;
  user_message: string;
  reply: string;
  emotion: string;
  created_at: string;
}

export interface ChatTurnListResponse {
  session_id: string;
  turns: ChatTurnRecord[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  emotion?: string;
}
