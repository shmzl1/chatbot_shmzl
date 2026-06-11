export interface ScheduleTaskPreview {
  id: string;
  title: string;
  status: "pending" | "done" | "delayed" | "skipped";
  date: string;
}
