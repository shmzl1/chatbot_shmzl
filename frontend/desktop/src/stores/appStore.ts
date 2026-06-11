import { create } from "zustand";
import { getBackendUrl, setBackendUrl } from "../api/client";

export type AppView = "chat" | "diary" | "schedule" | "settings";

export interface SelectedDiaryContext {
  id: number;
  title: string;
}

interface AppState {
  activeView: AppView;
  backendUrl: string;
  selectedDiary: SelectedDiaryContext | null;
  pendingChatDraft: string;
  setActiveView: (view: AppView) => void;
  updateBackendUrl: (value: string) => void;
  setSelectedDiary: (diary: SelectedDiaryContext | null) => void;
  setPendingChatDraft: (value: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activeView: "chat",
  backendUrl: getBackendUrl(),
  selectedDiary: null,
  pendingChatDraft: "",
  setActiveView: (view) => set({ activeView: view }),
  updateBackendUrl: (value) => {
    const backendUrl = setBackendUrl(value);
    set({ backendUrl });
  },
  setSelectedDiary: (diary) => set({ selectedDiary: diary }),
  setPendingChatDraft: (value) => set({ pendingChatDraft: value }),
}));
