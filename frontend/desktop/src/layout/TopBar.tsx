import { AlertTriangle, RotateCcw, Settings } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "../api/userApi";
import { useAppStore } from "../stores/appStore";
import { Button } from "../components/ui/Button";

const titles = {
  chat: "聊天",
  diary: "日记",
  schedule: "日程",
  settings: "设置",
};

export function TopBar() {
  const activeView = useAppStore((state) => state.activeView);
  const backendUrl = useAppStore((state) => state.backendUrl);
  const setActiveView = useAppStore((state) => state.setActiveView);
  const healthQuery = useQuery({
    queryKey: ["health", backendUrl],
    queryFn: getHealth,
    retry: 0,
  });
  const showServiceError = healthQuery.isError;

  return (
    <header className="top-bar">
      <div>
        <h1 className="text-3xl font-black text-[var(--ink)]">{titles[activeView]}</h1>
      </div>
      {showServiceError ? (
        <div className="service-error-notice">
          <AlertTriangle size={16} />
          <span>无法连接服务，请检查后端是否已启动。</span>
          <Button className="h-8 min-h-8 px-3" variant="ghost" type="button" onClick={() => void healthQuery.refetch()}>
            <RotateCcw size={14} />
            重试
          </Button>
          <Button className="h-8 min-h-8 px-3" variant="ghost" type="button" onClick={() => setActiveView("settings")}>
            <Settings size={14} />
            前往设置
          </Button>
        </div>
      ) : null}
    </header>
  );
}
