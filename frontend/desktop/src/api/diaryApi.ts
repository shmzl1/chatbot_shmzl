import { requestJson } from "./client";
import type {
  DiaryEntryDetail,
  DiaryEntryListResponse,
  DiaryEntryPayload,
  DiaryFilters,
  DiaryImageUploadResponse,
} from "../types/diary";

export function listDiaryEntries(filters: DiaryFilters = {}): Promise<DiaryEntryListResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  const query = params.toString();
  return requestJson<DiaryEntryListResponse>(`/diary/entries${query ? `?${query}` : ""}`);
}

export function createDiaryEntry(payload: DiaryEntryPayload): Promise<DiaryEntryDetail> {
  return requestJson<DiaryEntryDetail>("/diary/entries", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getDiaryEntry(entryId: number): Promise<DiaryEntryDetail> {
  return requestJson<DiaryEntryDetail>(`/diary/entries/${entryId}`);
}

export function updateDiaryEntry(entryId: number, payload: DiaryEntryPayload): Promise<DiaryEntryDetail> {
  return requestJson<DiaryEntryDetail>(`/diary/entries/${entryId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteDiaryEntry(entryId: number): Promise<{ status: string; deleted: number }> {
  return requestJson<{ status: string; deleted: number }>(`/diary/entries/${entryId}`, {
    method: "DELETE",
  });
}

export function uploadDiaryImage(entryId: number, file: File): Promise<DiaryImageUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson<DiaryImageUploadResponse>(`/diary/entries/${entryId}/images`, {
    method: "POST",
    body: formData,
  });
}

export function deleteDiaryImage(imageId: number): Promise<{ status: string; deleted: number }> {
  return requestJson<{ status: string; deleted: number }>(`/diary/images/${imageId}`, {
    method: "DELETE",
  });
}
