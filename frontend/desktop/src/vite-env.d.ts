/// <reference types="vite/client" />

interface Window {
  desktopShell?: {
    platform: string;
    windowControl?: (action: "minimize" | "maximize" | "close") => void;
  };
}
