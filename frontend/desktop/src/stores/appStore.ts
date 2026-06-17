import { create } from "zustand";
import { getBackendUrl, setBackendUrl } from "../api/client";

export type AppView = "chat" | "diary" | "schedule" | "settings";
const SELECTED_CHARACTER_STORAGE_KEY = "chatbot.selectedCharacterId";

export interface SelectedDiaryContext {
  id: number;
  title: string;
}

interface AppState {
  activeView: AppView;
  backendUrl: string;
  selectedCharacterId: string | null;
  selectedDiary: SelectedDiaryContext | null;
  pendingChatDraft: string;
  setActiveView: (view: AppView) => void;
  updateBackendUrl: (value: string) => void;
  setSelectedCharacterId: (characterId: string | null) => void;
  setSelectedDiary: (diary: SelectedDiaryContext | null) => void;
  setPendingChatDraft: (value: string) => void;
}

function getStoredCharacterId(): string | null {
  return window.localStorage.getItem(SELECTED_CHARACTER_STORAGE_KEY) || null;
}

function setStoredCharacterId(characterId: string | null) {
  if (characterId) {
    window.localStorage.setItem(SELECTED_CHARACTER_STORAGE_KEY, characterId);
    return;
  }
  window.localStorage.removeItem(SELECTED_CHARACTER_STORAGE_KEY);
}

export const useAppStore = create<AppState>((set) => ({
  activeView: "chat",
  backendUrl: getBackendUrl(),
  selectedCharacterId: getStoredCharacterId(),
  selectedDiary: null,
  pendingChatDraft: "",
  setActiveView: (view) => set({ activeView: view }),
  updateBackendUrl: (value) => {
    const backendUrl = setBackendUrl(value);
    set({ backendUrl });
  },
  setSelectedCharacterId: (characterId) => {
    setStoredCharacterId(characterId);
    set({ selectedCharacterId: characterId });
  },
  setSelectedDiary: (diary) => set({ selectedDiary: diary }),
  setPendingChatDraft: (value) => set({ pendingChatDraft: value }),
}));
