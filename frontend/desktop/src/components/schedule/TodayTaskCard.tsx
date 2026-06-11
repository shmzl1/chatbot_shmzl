import { Check, Clock3, FastForward } from "lucide-react";
import { Button } from "../ui/Button";

export function TodayTaskCard() {
  return (
    <section className="note-card rounded-[24px] p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--muted)]">Today</p>
          <h3 className="mt-1 text-xl font-black">今日任务</h3>
        </div>
        <span className="rounded-full bg-[rgba(188,139,79,0.14)] px-3 py-1 text-xs font-black text-[var(--gold)]">
          日程后端暂未实现
        </span>
      </div>
      <div className="grid gap-3">
        <div className="rounded-2xl border border-dashed border-[var(--line)] bg-[rgba(255,250,241,0.64)] p-5 text-sm leading-6 text-[var(--muted)]">
          日程页先保留桌面端结构：今日任务、任务状态、计划卡片和月历视图。后端接口实现后再接真实数据。
        </div>
        <div className="flex flex-wrap gap-2">
          <Button disabled variant="secondary">
            <Check size={16} />
            完成
          </Button>
          <Button disabled variant="secondary">
            <Clock3 size={16} />
            延期
          </Button>
          <Button disabled variant="secondary">
            <FastForward size={16} />
            跳过
          </Button>
        </div>
      </div>
    </section>
  );
}
