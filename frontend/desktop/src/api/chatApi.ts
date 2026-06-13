import { requestJson } from "./client";
import type {
  CharacterListResponse,
  ChatSessionListResponse,
  ChatTextRequest,
  ChatTextResponse,
  ChatTurnListResponse,
} from "../types/chat";

export function listCharacters(): Promise<CharacterListResponse> {
  return requestJson<CharacterListResponse>("/characters");
}

export function sendChatMessage(request: ChatTextRequest): Promise<ChatTextResponse> {
  return requestJson<ChatTextResponse>("/chat/text", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function listChatSessions(limit = 30): Promise<ChatSessionListResponse> {
  return requestJson<ChatSessionListResponse>(`/debug/sessions?limit=${limit}`);
}

export function listChatTurns(sessionId: string): Promise<ChatTurnListResponse> {
  return requestJson<ChatTurnListResponse>(`/debug/sessions/${encodeURIComponent(sessionId)}/turns`);
}
