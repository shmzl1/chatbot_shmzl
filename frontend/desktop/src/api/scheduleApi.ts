import { requestJson } from "./client";
import type {
  ScheduleCalendarResponse,
  ScheduleDayResponse,
  ScheduleFilters,
  ScheduleItemDetail,
  ScheduleItemListResponse,
  ScheduleItemPayload,
  SchedulePostponePayload,
  SchedulePostponeResponse,
} from "../types/schedule";

function buildQuery(params: object): string {
  const query = new URLSearchParams();
  Object.entries(params as Record<string, unknown>).forEach(([key, value]) => {
    if ((typeof value === "string" || typeof value === "number") && value !== "") {
      query.set(key, String(value));
    }
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function listScheduleItems(filters: ScheduleFilters = {}): Promise<ScheduleItemListResponse> {
  return requestJson<ScheduleItemListResponse>(`/schedule/items${buildQuery(filters)}`);
}

export function createScheduleItem(payload: ScheduleItemPayload): Promise<ScheduleItemDetail> {
  return requestJson<ScheduleItemDetail>("/schedule/items", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getScheduleItem(itemId: number): Promise<ScheduleItemDetail> {
  return requestJson<ScheduleItemDetail>(`/schedule/items/${itemId}`);
}

export function updateScheduleItem(itemId: number, payload: ScheduleItemPayload): Promise<ScheduleItemDetail> {
  return requestJson<ScheduleItemDetail>(`/schedule/items/${itemId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteScheduleItem(itemId: number): Promise<{ status: string; deleted: number }> {
  return requestJson<{ status: string; deleted: number }>(`/schedule/items/${itemId}`, {
    method: "DELETE",
  });
}

export function getScheduleDay(params: {
  date?: string;
  item_type?: string;
  status?: string;
}): Promise<ScheduleDayResponse> {
  return requestJson<ScheduleDayResponse>(`/schedule/today${buildQuery(params)}`);
}

export function getScheduleCalendar(month: string): Promise<ScheduleCalendarResponse> {
  return requestJson<ScheduleCalendarResponse>(`/schedule/calendar${buildQuery({ month })}`);
}

export function completeScheduleOccurrence(occurrenceId: number): Promise<ScheduleItemDetail> {
  return requestJson<ScheduleItemDetail>(`/schedule/occurrences/${occurrenceId}/complete`, {
    method: "POST",
  });
}

export function skipScheduleOccurrence(occurrenceId: number): Promise<ScheduleItemDetail> {
  return requestJson<ScheduleItemDetail>(`/schedule/occurrences/${occurrenceId}/skip`, {
    method: "POST",
  });
}

export function postponeScheduleOccurrence(
  occurrenceId: number,
  payload: SchedulePostponePayload,
): Promise<SchedulePostponeResponse> {
  return requestJson<SchedulePostponeResponse>(`/schedule/occurrences/${occurrenceId}/postpone`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
