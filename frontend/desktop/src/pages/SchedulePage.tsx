import { CalendarDays } from "lucide-react";
import { CalendarSkeleton } from "../components/schedule/CalendarSkeleton";
import { TodayTaskCard } from "../components/schedule/TodayTaskCard";
import { EmptyState } from "../components/ui/EmptyState";
import { StickyCard } from "../components/paper/StickyCard";
import { scheduleBackendStatus } from "../api/scheduleApi";

export function SchedulePage() {
  const status = scheduleBackendStatus();

  return (
    <div className="grid h-full grid-cols-[240px_minmax(520px,1fr)_280px] gap-5">
      <aside className="soft-panel rounded-[28px] p-4">
        <h2 className="mb-4 text-xl font-black">计划</h2>
        <EmptyState icon={<CalendarDays size={22} />} title="没有计划数据" description={status.message} />
      </aside>
      <section className="min-h-0 overflow-auto">
        <div className="grid gap-5">
          <TodayTaskCard />
          <CalendarSkeleton />
        </div>
      </section>
      <aside className="soft-panel rounded-[28px] p-4">
        <h2 className="mb-4 text-xl font-black">任务详情</h2>
        <div className="grid gap-3">
          {["待处理", "已完成", "已延期", "已跳过"].map((label) => (
            <StickyCard key={label}>
              <div className="flex items-center justify-between">
                <strong className="text-sm">{label}</strong>
                <span className="rounded-full bg-[rgba(97,123,149,0.12)] px-2 py-1 text-xs font-black text-[var(--blue)]">0</span>
              </div>
            </StickyCard>
          ))}
        </div>
      </aside>
    </div>
  );
}
