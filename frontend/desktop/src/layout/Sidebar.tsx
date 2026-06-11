import { BookOpen, CalendarDays, MessageCircle, Settings } from "lucide-react";
import { clsx } from "clsx";
import type { ComponentType } from "react";
import { useAppStore, type AppView } from "../stores/appStore";

const items: Array<{ id: AppView; label: string; icon: ComponentType<{ size?: number }> }> = [
  { id: "chat", label: "聊天", icon: MessageCircle },
  { id: "diary", label: "日记", icon: BookOpen },
  { id: "schedule", label: "日程", icon: CalendarDays },
  { id: "settings", label: "设置", icon: Settings },
];

export function Sidebar() {
  const activeView = useAppStore((state) => state.activeView);
  const setActiveView = useAppStore((state) => state.setActiveView);

  return (
    <aside className="soft-panel flex h-full w-[92px] flex-col items-center gap-4 rounded-r-[28px] px-3 py-6">
      <div className="mb-4 grid size-12 place-items-center rounded-2xl bg-[var(--green)] text-lg font-black text-white shadow-soft">
        朝
      </div>
      <nav className="grid w-full gap-2">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              className={clsx(
                "grid h-[70px] place-items-center rounded-2xl text-xs font-black transition",
                activeView === item.id
                  ? "bg-[var(--surface)] text-[var(--green)] shadow-soft"
                  : "text-[var(--muted)] hover:bg-[rgba(255,250,241,0.68)] hover:text-[var(--ink)]",
              )}
              type="button"
              onClick={() => setActiveView(item.id)}
            >
              <Icon size={22} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
