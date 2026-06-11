import { create } from "zustand";
import type { ChatMessage } from "../types/chat";

interface ChatState {
  sessionId: string | null;
  messages: ChatMessage[];
  setSessionId: (sessionId: string | null) => void;
  appendMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  sessionId: null,
  messages: [],
  setSessionId: (sessionId) => set({ sessionId }),
  appendMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  clearMessages: () => set({ messages: [], sessionId: null }),
}));
