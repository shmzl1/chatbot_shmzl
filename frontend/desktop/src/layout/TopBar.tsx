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
  const statusText = online ? "服务正常" : "服务未连接";

  return (
    <header className="top-bar">
      <div>
        <h1 className="text-3xl font-black text-[var(--ink)]">{titles[activeView]}</h1>
      </div>
      <div className="service-status-pill" title={statusText}>
        {online ? <Wifi className="text-[var(--green)]" size={18} /> : <WifiOff className="text-[var(--danger)]" size={18} />}
        <span>{statusText}</span>
      </div>
    </header>
  );
}
