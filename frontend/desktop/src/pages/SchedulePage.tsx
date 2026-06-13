import { CalendarDays, Check, Clock3, FastForward, Layers3 } from "lucide-react";
import { CalendarSkeleton } from "../components/schedule/CalendarSkeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { scheduleBackendStatus } from "../api/scheduleApi";

export function SchedulePage() {
  const status = scheduleBackendStatus();

  return (
    <div className="schedule-workspace">
      <aside className="schedule-plan-rail">
        <div className="page-kicker">
          <span>Plans</span>
          <strong>计划</strong>
        </div>
        <div className="schedule-plan-card muted">
          <Layers3 size={18} />
          <div>
            <strong>本地计划接口未接入</strong>
            <small>{status.message}</small>
          </div>
        </div>
        <div className="schedule-filter-stack">
          {["全部", "学习", "事项", "复习"].map((label, index) => (
            <button className={index === 0 ? "active" : ""} type="button" key={label}>
              <span>{label}</span>
              <em>0</em>
            </button>
          ))}
        </div>
      </aside>

      <section className="schedule-main">
        <div className="schedule-hero">
          <div>
            <p className="eyebrow">Today</p>
            <h2>今日任务</h2>
            <p>后端日程模块接入前，这里保留真实工作区结构，不生成假任务。</p>
          </div>
          <div className="schedule-progress-ring">
            <strong>0</strong>
            <span>待处理</span>
          </div>
        </div>

        <div className="today-task-shell">
          <div className="today-task-header">
            <h3>等待处理的内容</h3>
            <div className="segmented-filter">
              {["全部", "知识点", "事项"].map((label, index) => (
                <button className={index === 0 ? "active" : ""} type="button" key={label}>
                  {label}
                </button>
              ))}
            </div>
          </div>
          <EmptyState icon={<CalendarDays size={24} />} title="今天没有任务" description={status.message} />
          <div className="schedule-action-row">
            <button disabled type="button">
              <Check size={15} />
              完成
            </button>
            <button disabled type="button">
              <Clock3 size={15} />
              延期
            </button>
            <button disabled type="button">
              <FastForward size={15} />
              跳过
            </button>
          </div>
        </div>

        <div className="schedule-calendar-shell">
          <CalendarSkeleton />
        </div>
      </section>

      <aside className="schedule-detail-panel">
        <div className="page-kicker">
          <span>Review</span>
          <strong>任务详情</strong>
        </div>
        <div className="status-pill-grid">
          {["待处理", "已完成", "已延期", "已跳过"].map((label) => (
            <div className="status-pill" key={label}>
              <span>{label}</span>
              <strong>0</strong>
            </div>
          ))}
        </div>
        <div className="review-feedback-card">
          <p className="eyebrow">Feedback</p>
          <h3>复习反馈</h3>
          <p>接口接入后，这里会显示“记住 / 模糊 / 没记住 / 跳过”等反馈操作。</p>
        </div>
      </aside>
    </div>
  );
}
