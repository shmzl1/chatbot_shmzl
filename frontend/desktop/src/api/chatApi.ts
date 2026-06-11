import { requestJson } from "./client";
import type { CharacterListResponse, ChatTextRequest, ChatTextResponse } from "../types/chat";

export function listCharacters(): Promise<CharacterListResponse> {
  return requestJson<CharacterListResponse>("/characters");
}

export function sendChatMessage(request: ChatTextRequest): Promise<ChatTextResponse> {
  return requestJson<ChatTextResponse>("/chat/text", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
