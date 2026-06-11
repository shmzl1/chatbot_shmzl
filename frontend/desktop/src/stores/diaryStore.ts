import { create } from "zustand";

interface DiaryState {
  activeEntryId: number | null;
  setActiveEntryId: (entryId: number | null) => void;
}

export const useDiaryStore = create<DiaryState>((set) => ({
  activeEntryId: null,
  setActiveEntryId: (entryId) => set({ activeEntryId: entryId }),
}));
