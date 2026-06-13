import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("desktopShell", {
  platform: process.platform,
  windowControl: (action: "minimize" | "maximize" | "close") => {
    ipcRenderer.send("window:control", action);
  },
});
