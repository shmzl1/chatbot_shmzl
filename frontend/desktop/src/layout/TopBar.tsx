import { Wifi, WifiOff } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "../api/userApi";
import { useAppStore } from "../stores/appStore";

const titles = {
  chat: "聊天",
  diary: "日记",
  schedule: "日程",
  settings: "设置",
};

export function TopBar() {
  const activeView = useAppStore((state) => state.activeView);
  const backendUrl = useAppStore((state) => state.backendUrl);
  const healthQuery = useQuery({
    queryKey: ["health", backendUrl],
    queryFn: getHealth,
    retry: 0,
  });

  const online = healthQuery.data?.status === "ok";

  return (
    <header className="flex h-20 items-center justify-between px-8">
      <div>
        <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--muted)]">Local Desktop</p>
        <h1 className="mt-1 text-3xl font-black text-[var(--ink)]">{titles[activeView]}</h1>
      </div>
      <div className="flex items-center gap-3 rounded-2xl border border-[var(--line)] bg-[rgba(255,250,241,0.72)] px-4 py-2 text-sm font-bold text-[var(--muted)]">
        {online ? <Wifi className="text-[var(--green)]" size={18} /> : <WifiOff className="text-[var(--danger)]" size={18} />}
        <span>{backendUrl}</span>
      </div>
    </header>
  );
}
