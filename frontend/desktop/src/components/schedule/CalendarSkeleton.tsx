const days = Array.from({ length: 35 }, (_, index) => index + 1);

export function CalendarSkeleton() {
  return (
    <div className="paper-sheet rounded-[24px] p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-black">月历</h3>
        <span className="rounded-full bg-[rgba(97,123,149,0.12)] px-3 py-1 text-xs font-black text-[var(--blue)]">骨架</span>
      </div>
      <div className="grid grid-cols-7 gap-2">
        {["一", "二", "三", "四", "五", "六", "日"].map((day) => (
          <div className="text-center text-xs font-black text-[var(--muted)]" key={day}>
            {day}
          </div>
        ))}
        {days.map((day) => (
          <div className="min-h-[72px] rounded-2xl border border-[var(--line)] bg-[rgba(255,255,255,0.42)] p-2 text-xs font-bold text-[var(--muted)]" key={day}>
            {day}
          </div>
        ))}
      </div>
    </div>
  );
}
