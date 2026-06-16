@echo off
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"

echo.
echo 虚拟人物陪伴系统 - 暂时暂停
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
echo 已暂时暂停。
echo 本项目默认使用本地 SQLite 文件：backend\data\chatbot.db。
echo 没有执行容器命令、没有删除数据库文件、没有删除上传文件。
echo 没有执行 wsl --shutdown。
echo.
pause
