import { AppShell } from "./layout/AppShell";
import { ErrorBoundary } from "./components/ui/ErrorBoundary";

export default function App() {
  return (
    <ErrorBoundary scope="应用">
      <AppShell />
    </ErrorBoundary>
  );
}
