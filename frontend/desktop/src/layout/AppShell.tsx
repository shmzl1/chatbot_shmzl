import { ChatPage } from "../pages/ChatPage";
import { DiaryPage } from "../pages/DiaryPage";
import { SchedulePage } from "../pages/SchedulePage";
import { SettingsPage } from "../pages/SettingsPage";
import { ErrorBoundary } from "../components/ui/ErrorBoundary";
import { useAppStore } from "../stores/appStore";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { WindowFrame } from "./WindowFrame";

export function AppShell() {
  const activeView = useAppStore((state) => state.activeView);
  const pageTitle = {
    chat: "聊天",
    diary: "日记",
    schedule: "日程",
    settings: "设置",
  }[activeView];

  return (
    <div className="app-frame">
      <WindowFrame />
      <div className="app-body">
        <Sidebar />
        <main className="app-main">
          <TopBar />
          <section className="content-shell">
            <ErrorBoundary key={activeView} scope={pageTitle}>
              {activeView === "chat" ? <ChatPage /> : null}
              {activeView === "diary" ? <DiaryPage /> : null}
              {activeView === "schedule" ? <SchedulePage /> : null}
              {activeView === "settings" ? <SettingsPage /> : null}
            </ErrorBoundary>
          </section>
        </main>
      </div>
    </div>
  );
}
