import { Check, Clock3, FastForward } from "lucide-react";
import type { ScheduleItemSummary } from "../../types/schedule";
import { schedulePriorityLabels, scheduleStatusLabels, scheduleTypeLabels } from "../../types/schedule";

interface TodayTaskCardProps {
  item: ScheduleItemSummary;
  onComplete: () => void;
  onPostpone: () => void;
  onSkip: () => void;
}

export function TodayTaskCard({ item, onComplete, onPostpone, onSkip }: TodayTaskCardProps) {
  const isActionable = item.current_occurrence.status === "pending" || item.current_occurrence.status === "overdue";

  return (
    <section className={`schedule-task-card ${item.current_occurrence.status}`}>
      <div className="schedule-task-head">
        <strong>{item.title}</strong>
        <span className={`schedule-status ${item.current_occurrence.status}`}>
          {scheduleStatusLabels[item.current_occurrence.status]}
        </span>
      </div>
      <p>{item.note || "没有备注"}</p>
      <div className="schedule-task-meta">
        <span>{scheduleTypeLabels[item.item_type]}</span>
        <span>{schedulePriorityLabels[item.priority]}</span>
        <span>{item.current_occurrence.scheduled_time || "全天"}</span>
        {item.estimated_minutes ? <span>{item.estimated_minutes} 分钟</span> : null}
      </div>
      {item.tags.length ? (
        <div className="schedule-tag-preview">
          {item.tags.slice(0, 4).map((tag) => <span key={tag}>{tag}</span>)}
        </div>
      ) : null}
      {isActionable ? (
        <div className="schedule-action-row">
          <button type="button" onClick={onComplete}>
            <Check size={16} />
            完成
          </button>
          <button type="button" onClick={onPostpone}>
            <Clock3 size={16} />
            延期
          </button>
          <button type="button" onClick={onSkip}>
            <FastForward size={16} />
            跳过
          </button>
        </div>
      ) : null}
    </section>
  );
}
