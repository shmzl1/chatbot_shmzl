import { app, BrowserWindow, ipcMain, shell } from "electron";
import path from "node:path";
import { fileURLToPath } from "node:url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 1360,
        height: 880,
        minWidth: 1024,
        minHeight: 700,
        title: "虚拟人物陪伴系统",
        backgroundColor: "#f5f1e8",
        show: false,
        resizable: true,
        maximizable: true,
        minimizable: true,
        fullscreenable: true,
        thickFrame: true,
        autoHideMenuBar: true,
        titleBarStyle: "hidden",
        titleBarOverlay: {
            color: "#f3efe6",
            symbolColor: "#2b2924",
            height: 36,
        },
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    const devServerUrl = process.env.VITE_DEV_SERVER_URL;
    if (devServerUrl) {
        void mainWindow.loadURL(devServerUrl);
    }
    else {
        void mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
    }
    mainWindow.once("ready-to-show", () => {
        mainWindow.show();
        mainWindow.focus();
    });
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        void shell.openExternal(url);
        return { action: "deny" };
    });
}
ipcMain.on("window:control", (event, action) => {
    const window = BrowserWindow.fromWebContents(event.sender);
    if (!window) {
        return;
    }
    if (action === "minimize") {
        window.minimize();
    }
    if (action === "maximize") {
        if (window.isMaximized()) {
            window.unmaximize();
        }
        else {
            window.maximize();
        }
    }
    if (action === "close") {
        window.close();
    }
});
app.whenReady().then(() => {
    createWindow();
    app.on("activate", () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});
app.on("window-all-closed", () => {
    if (process.platform !== "darwin") {
        app.quit();
    }
});
