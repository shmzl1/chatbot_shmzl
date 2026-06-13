import { contextBridge, ipcRenderer } from "electron";
contextBridge.exposeInMainWorld("desktopShell", {
    platform: process.platform,
    windowControl: (action) => {
        ipcRenderer.send("window:control", action);
    },
});
