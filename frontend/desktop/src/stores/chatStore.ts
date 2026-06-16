import { create } from "zustand";
import type { ChatMessage } from "../types/chat";

export type ConversationMode = "new" | "existing" | "archived";
export type SessionListMode = "active" | "archived";

interface ChatState {
  activeSessionId: string | null;
  conversationMode: ConversationMode;
  sessionSidebarOpen: boolean;
  sessionSearch: string;
  sessionListMode: SessionListMode;
  messages: ChatMessage[];
  setActiveSessionId: (sessionId: string | null) => void;
  selectSession: (sessionId: string, mode: ConversationMode) => void;
  startNewConversation: () => void;
  setSessionSidebarOpen: (open: boolean) => void;
  setSessionSearch: (value: string) => void;
  setSessionListMode: (mode: SessionListMode) => void;
  setMessages: (messages: ChatMessage[]) => void;
  appendMessage: (message: ChatMessage) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  activeSessionId: null,
  conversationMode: "new",
  sessionSidebarOpen: false,
  sessionSearch: "",
  sessionListMode: "active",
  messages: [],
  setActiveSessionId: (sessionId) =>
    set({
      activeSessionId: sessionId,
      conversationMode: sessionId ? "existing" : "new",
    }),
  selectSession: (sessionId, mode) =>
    set({
      activeSessionId: sessionId,
      conversationMode: mode,
      messages: [],
      sessionSidebarOpen: false,
    }),
  startNewConversation: () =>
    set({
      activeSessionId: null,
      conversationMode: "new",
      messages: [],
      sessionListMode: "active",
      sessionSidebarOpen: false,
    }),
  setSessionSidebarOpen: (open) => set({ sessionSidebarOpen: open }),
  setSessionSearch: (value) => set({ sessionSearch: value }),
  setSessionListMode: (mode) => set({ sessionListMode: mode }),
  setMessages: (messages) => set({ messages }),
  appendMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
}));
