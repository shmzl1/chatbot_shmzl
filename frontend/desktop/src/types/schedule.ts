export type ScheduleItemType = "task" | "study_point" | "review_point" | "habit";
export type ScheduleOccurrenceStatus = "pending" | "done" | "skipped" | "postponed" | "overdue";

export interface ScheduleItemPayload {
  title: string;
  note: string;
  item_type: ScheduleItemType;
  priority: number;
  tags: string[];
  estimated_minutes: number | null;
  scheduled_date: string;
  scheduled_time: string | null;
}

export interface ScheduleOccurrence {
  id: number;
  item_id: number;
  scheduled_date: string;
  scheduled_time?: string | null;
  status: ScheduleOccurrenceStatus;
  completed_at?: string | null;
  source_occurrence_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduleItemSummary {
  id: number;
  title: string;
  note: string;
  item_type: ScheduleItemType;
  priority: number;
  tags: string[];
  estimated_minutes?: number | null;
  current_occurrence: ScheduleOccurrence;
  created_at: string;
  updated_at: string;
}

export interface ScheduleItemDetail extends ScheduleItemSummary {
  occurrences: ScheduleOccurrence[];
}

export interface ScheduleItemListResponse {
  items: ScheduleItemSummary[];
  total: number;
}

export interface ScheduleStatusCounts {
  pending: number;
  done: number;
  skipped: number;
  postponed: number;
  overdue: number;
}

export interface ScheduleTypeCounts {
  task: number;
  study_point: number;
  review_point: number;
  habit: number;
}

export interface ScheduleDayResponse {
  date: string;
  occurrences: ScheduleItemSummary[];
  status_counts: ScheduleStatusCounts;
  type_counts: ScheduleTypeCounts;
  total: number;
  completion_rate: number;
}

export interface ScheduleCalendarDay {
  date: string;
  total: number;
  pending: number;
  done: number;
  skipped: number;
  postponed: number;
  overdue: number;
}

export interface ScheduleCalendarResponse {
  month: string;
  days: ScheduleCalendarDay[];
}

export interface SchedulePostponePayload {
  scheduled_date: string;
  scheduled_time?: string | null;
}

export interface SchedulePostponeResponse {
  old_occurrence: ScheduleOccurrence;
  new_occurrence: ScheduleOccurrence;
  item: ScheduleItemDetail;
}

export interface ScheduleFilters {
  keyword?: string;
  item_type?: ScheduleItemType | "";
  status?: ScheduleOccurrenceStatus | "";
  tag?: string;
  priority?: number | "";
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

export const scheduleStatusLabels: Record<ScheduleOccurrenceStatus, string> = {
  pending: "待处理",
  done: "已完成",
  skipped: "已跳过",
  postponed: "已延期",
  overdue: "已逾期",
};

export const scheduleTypeLabels: Record<ScheduleItemType, string> = {
  task: "事项",
  study_point: "学习",
  review_point: "复习",
  habit: "习惯",
};

export const schedulePriorityLabels: Record<number, string> = {
  1: "最高",
  2: "高",
  3: "普通",
  4: "低",
  5: "最低",
};
