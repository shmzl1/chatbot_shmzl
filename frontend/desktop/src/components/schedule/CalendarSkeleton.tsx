import { ChevronLeft, ChevronRight } from "lucide-react";

const days = Array.from({ length: 35 }, (_, index) => index + 1);

export function CalendarSkeleton() {
  return (
    <div className="month-calendar-card">
      <div className="month-calendar-head">
        <div>
          <p className="eyebrow">Month</p>
          <h3>月任务</h3>
        </div>
        <div className="month-controls">
          <button disabled type="button" aria-label="上个月">
            <ChevronLeft size={16} />
          </button>
          <strong>本月</strong>
          <button disabled type="button" aria-label="下个月">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
      <div className="month-calendar-grid">
        {["日", "一", "二", "三", "四", "五", "六"].map((day) => (
          <div className="month-weekday" key={day}>
            {day}
          </div>
        ))}
        {days.map((day) => (
          <div className={`month-day-cell ${day === 13 ? "today" : ""}`} key={day}>
            <header>
              <span>{day}</span>
              <small>0/0</small>
            </header>
            <div className="month-empty-line" />
          </div>
        ))}
      </div>
    </div>
  );
}
