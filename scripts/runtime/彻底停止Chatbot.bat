@echo off
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"

echo.
echo 虚拟人物陪伴系统 - 彻底停止
echo 项目目录：%PROJECT_ROOT%
echo.

echo 正在停止监听 8000 的后端进程...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>nul
)

echo 正在停止监听 9880 的 GPT-SoVITS API 进程（如果存在）...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":9880" ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>nul
)

echo.
echo 即将执行 wsl --shutdown。
echo 注意：这会关闭所有 WSL，包括 Docker Desktop 后端和其他 WSL 终端。
echo 不删除本地 SQLite 数据库文件 backend\data\chatbot.db。
echo 不删除上传文件 backend\data\uploads。
echo.
wsl --shutdown

echo.
echo 已彻底停止并释放 WSL 占用的内存。
echo SQLite 数据库文件已保留。
echo.
pause
