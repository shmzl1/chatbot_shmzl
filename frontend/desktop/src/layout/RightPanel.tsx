import { BookMarked, CircleUserRound, Database, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getMe } from "../api/userApi";
import { resolveAssetUrl } from "../api/client";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { StickyCard } from "../components/paper/StickyCard";
import { useAppStore } from "../stores/appStore";

export function RightPanel() {
  const selectedDiary = useAppStore((state) => state.selectedDiary);
  const setSelectedDiary = useAppStore((state) => state.setSelectedDiary);
  const userQuery = useQuery({ queryKey: ["me"], queryFn: getMe });
  const user = userQuery.data;

  return (
    <aside className="hidden h-full w-[320px] shrink-0 flex-col gap-4 overflow-auto px-5 py-6 xl:flex">
      <StickyCard>
        <div className="flex items-center gap-3">
          {user?.avatar_url ? (
            <img className="size-12 rounded-2xl object-cover" src={resolveAssetUrl(user.avatar_url)} alt={user.username} />
          ) : (
            <div className="grid size-12 place-items-center rounded-2xl bg-[rgba(98,119,90,0.15)] text-[var(--green)]">
              <CircleUserRound size={24} />
            </div>
          )}
          <div className="min-w-0">
            <p className="truncate text-base font-black">{user?.username || "我"}</p>
            <p className="text-xs font-bold text-[var(--muted)]">本地默认用户</p>
          </div>
        </div>
      </StickyCard>

      <StickyCard>
        <div className="mb-3 flex items-center gap-2 text-sm font-black">
          <BookMarked size={18} className="text-[var(--green)]" />
          当前上下文
        </div>
        {selectedDiary ? (
          <div className="grid gap-3">
            <p className="text-sm leading-6 text-[var(--muted)]">正在阅读：</p>
            <div className="rounded-xl bg-[rgba(98,119,90,0.1)] p-3 text-sm font-black text-[var(--green)]">
              {selectedDiary.title || "未命名日记"}
            </div>
            <Button variant="ghost" onClick={() => setSelectedDiary(null)}>
              <X size={16} />
              清空日记上下文
            </Button>
          </div>
        ) : (
          <EmptyState title="没有选中日记" description="普通聊天不会读取任何日记。" />
        )}
      </StickyCard>

      <StickyCard>
        <div className="mb-2 flex items-center gap-2 text-sm font-black">
          <Database size={18} className="text-[var(--blue)]" />
          嵌入能力
        </div>
        <p className="text-sm leading-6 text-[var(--muted)]">
          角色和记忆不是一级入口。它们会在聊天、日记、日程中按需调用，并在设置中管理。
        </p>
      </StickyCard>
    </aside>
  );
}
