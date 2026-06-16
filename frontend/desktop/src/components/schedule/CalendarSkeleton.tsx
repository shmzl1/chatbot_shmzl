import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "../ui/Button";
import type { ScheduleCalendarDay } from "../../types/schedule";
import { formatMonthKey, getMonthGrid, getMonthLabel, isToday, shiftMonth } from "../../utils/date";

interface MonthCalendarProps {
  month: string;
  selectedDate: string;
  days: ScheduleCalendarDay[];
  isLoading?: boolean;
  error?: string;
  onMonthChange: (month: string) => void;
  onDateSelect: (date: string) => void;
  onRetry?: () => void;
}

const weekDays = ["日", "一", "二", "三", "四", "五", "六"];

export function MonthCalendar({
  month,
  selectedDate,
  days,
  isLoading,
  error,
  onMonthChange,
  onDateSelect,
  onRetry,
}: MonthCalendarProps) {
  const dayMap = new Map(days.map((day) => [day.date, day]));
  const grid = getMonthGrid(month);
  const currentMonth = formatMonthKey(new Date());

  return (
    <div className="month-calendar-card">
      <div className="month-calendar-head">
        <div>
          <p className="eyebrow">Month</p>
          <h3>{getMonthLabel(month)}</h3>
        </div>
        <div className="month-controls">
          <button type="button" aria-label="上个月" onClick={() => onMonthChange(shiftMonth(month, -1))}>
            <ChevronLeft size={16} />
          </button>
          <button className="month-today-button" type="button" onClick={() => onMonthChange(currentMonth)}>
            本月
          </button>
          <button type="button" aria-label="下个月" onClick={() => onMonthChange(shiftMonth(month, 1))}>
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {error ? (
        <div className="inline-error">
          <span>{error}</span>
          {onRetry ? (
            <Button className="ml-auto h-8 min-h-8 px-3" variant="ghost" type="button" onClick={onRetry}>
              重试
            </Button>
          ) : null}
        </div>
      ) : null}

      <div className="month-calendar-grid">
        {weekDays.map((day) => (
          <div className="month-weekday" key={day}>
            {day}
          </div>
        ))}
        {grid.map((day) => {
          const stats = dayMap.get(day.date);
          const total = stats?.total || 0;
          return (
            <button
              className={[
                "month-day-cell",
                day.inMonth ? "" : "muted",
                isToday(day.date) ? "today" : "",
                selectedDate === day.date ? "selected" : "",
              ].join(" ")}
              key={day.date}
              type="button"
              onClick={() => onDateSelect(day.date)}
            >
              <header>
                <span>{day.day}</span>
                <small>{isLoading ? "..." : `${stats?.done || 0}/${total}`}</small>
              </header>
              {isLoading ? (
                <div className="month-empty-line loading" />
              ) : total ? (
                <div className="month-day-marks">
                  {stats?.overdue ? <span className="overdue">逾 {stats.overdue}</span> : null}
                  {stats?.pending ? <span>待 {stats.pending}</span> : null}
                  {stats?.postponed ? <span>延 {stats.postponed}</span> : null}
                  {stats?.skipped ? <span>跳 {stats.skipped}</span> : null}
                </div>
              ) : (
                <div className="month-empty-line" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export const CalendarSkeleton = MonthCalendar;
