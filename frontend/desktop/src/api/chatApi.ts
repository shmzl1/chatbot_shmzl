import { requestJson } from "./client";
import type {
  CharacterListResponse,
  ChatSessionArchiveResponse,
  ChatSessionListResponse,
  ChatSessionSearchParams,
  ChatSessionUpdateRequest,
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

function buildQuery(params: object): string {
  const query = new URLSearchParams();
  Object.entries(params as Record<string, unknown>).forEach(([key, value]) => {
    if ((typeof value === "string" || typeof value === "number" || typeof value === "boolean") && value !== "") {
      query.set(key, String(value));
    }
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function listChatSessions(params: ChatSessionSearchParams = {}): Promise<ChatSessionListResponse> {
  return requestJson<ChatSessionListResponse>(`/chat/sessions${buildQuery(params)}`);
}

export function listChatTurns(sessionId: string): Promise<ChatTurnListResponse> {
  return requestJson<ChatTurnListResponse>(`/chat/sessions/${encodeURIComponent(sessionId)}/turns`);
}

export function renameChatSession(sessionId: string, request: ChatSessionUpdateRequest): Promise<ChatSessionArchiveResponse> {
  return requestJson<ChatSessionArchiveResponse>(`/chat/sessions/${encodeURIComponent(sessionId)}`, {
    method: "PATCH",
    body: JSON.stringify(request),
  });
}

export function archiveChatSession(sessionId: string): Promise<ChatSessionArchiveResponse> {
  return requestJson<ChatSessionArchiveResponse>(`/chat/sessions/${encodeURIComponent(sessionId)}/archive`, {
    method: "POST",
  });
}

export function unarchiveChatSession(sessionId: string): Promise<ChatSessionArchiveResponse> {
  return requestJson<ChatSessionArchiveResponse>(`/chat/sessions/${encodeURIComponent(sessionId)}/unarchive`, {
    method: "POST",
  });
}
