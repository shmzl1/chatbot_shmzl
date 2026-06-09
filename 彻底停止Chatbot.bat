@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo 虚拟人物陪伴系统 - 彻底停止
echo.

echo 正在停止监听 8000 的后端进程...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>nul
)

echo 正在停止监听 9880 的 GPT-SoVITS API 进程（如果存在）...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":9880" ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>nul
)

echo 正在执行 docker compose stop，保留数据库 volume...
docker compose stop

echo.
echo 即将执行 wsl --shutdown。
echo 注意：这会关闭所有 WSL，包括 Docker Desktop 后端和其他 WSL 终端。
echo 但不会执行 docker compose down -v，也不会删除 PostgreSQL volume。
echo.
wsl --shutdown

echo.
echo 已彻底停止并释放 WSL/Docker 占用的内存。
echo 数据库 volume 已保留。
echo.
pause
