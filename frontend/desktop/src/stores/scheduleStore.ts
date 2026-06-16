import { create } from "zustand";
import { formatLocalDate, formatMonthKey, parseLocalDate } from "../utils/date";
import type { ScheduleItemType, ScheduleOccurrenceStatus } from "../types/schedule";

export type ScheduleEditorMode = "closed" | "create" | "view" | "edit";

interface ScheduleState {
  selectedDate: string;
  selectedMonth: string;
  selectedItemId: number | null;
  selectedOccurrenceId: number | null;
  itemTypeFilter: ScheduleItemType | "";
  statusFilter: ScheduleOccurrenceStatus | "";
  editorMode: ScheduleEditorMode;
  setSelectedDate: (value: string) => void;
  setSelectedMonth: (value: string) => void;
  selectItem: (itemId: number, occurrenceId: number) => void;
  openCreate: () => void;
  openEdit: () => void;
  clearSelection: () => void;
  closeEditor: () => void;
  setItemTypeFilter: (value: ScheduleItemType | "") => void;
  setStatusFilter: (value: ScheduleOccurrenceStatus | "") => void;
}

const now = new Date();

export const useScheduleStore = create<ScheduleState>((set) => ({
  selectedDate: formatLocalDate(now),
  selectedMonth: formatMonthKey(now),
  selectedItemId: null,
  selectedOccurrenceId: null,
  itemTypeFilter: "",
  statusFilter: "",
  editorMode: "closed",
  setSelectedDate: (value) =>
    set({
      selectedDate: value,
      selectedMonth: formatMonthKey(parseLocalDate(value)),
    }),
  setSelectedMonth: (value) => set({ selectedMonth: value }),
  selectItem: (itemId, occurrenceId) =>
    set({
      selectedItemId: itemId,
      selectedOccurrenceId: occurrenceId,
      editorMode: "view",
    }),
  openCreate: () =>
    set({
      selectedItemId: null,
      selectedOccurrenceId: null,
      editorMode: "create",
    }),
  openEdit: () => set({ editorMode: "edit" }),
  clearSelection: () =>
    set({
      selectedItemId: null,
      selectedOccurrenceId: null,
      editorMode: "closed",
    }),
  closeEditor: () => set({ editorMode: "closed" }),
  setItemTypeFilter: (value) => set({ itemTypeFilter: value }),
  setStatusFilter: (value) => set({ statusFilter: value }),
}));
