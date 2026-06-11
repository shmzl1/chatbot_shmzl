import { ChatPage } from "../pages/ChatPage";
import { DiaryPage } from "../pages/DiaryPage";
import { SchedulePage } from "../pages/SchedulePage";
import { SettingsPage } from "../pages/SettingsPage";
import { useAppStore } from "../stores/appStore";
import { RightPanel } from "./RightPanel";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { WindowFrame } from "./WindowFrame";

export function AppShell() {
  const activeView = useAppStore((state) => state.activeView);

  return (
    <div className="h-screen overflow-hidden bg-[var(--app-bg)] pt-9">
      <WindowFrame />
      <div className="flex h-full">
        <Sidebar />
        <main className="flex min-w-0 flex-1 flex-col">
          <TopBar />
          <section className="min-h-0 flex-1 overflow-hidden px-8 pb-8">
            {activeView === "chat" ? <ChatPage /> : null}
            {activeView === "diary" ? <DiaryPage /> : null}
            {activeView === "schedule" ? <SchedulePage /> : null}
            {activeView === "settings" ? <SettingsPage /> : null}
          </section>
        </main>
        <RightPanel />
      </div>
    </div>
  );
}
