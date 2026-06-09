@echo off
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "COMPOSE_FILE=%PROJECT_ROOT%\deploy\docker\docker-compose.yml"

echo.
echo 虚拟人物陪伴系统 - 彻底停止
echo 项目目录：%PROJECT_ROOT%
echo Compose 文件：%COMPOSE_FILE%
echo.

echo 正在停止监听 8000 的后端进程...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>nul
)

echo 正在停止监听 9880 的 GPT-SoVITS API 进程（如果存在）...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":9880" ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>nul
)

echo 正在执行 Docker Compose stop，保留数据库 volume...
docker compose --project-directory "%PROJECT_ROOT%" -f "%COMPOSE_FILE%" stop

echo.
echo 即将执行 wsl --shutdown。
echo 注意：这会关闭所有 WSL，包括 Docker Desktop 后端和其他 WSL 终端。
echo 不执行 docker compose down。
echo 不执行 docker compose down -v。
echo 不删除 PostgreSQL volume。
echo.
wsl --shutdown

echo.
echo 已彻底停止并释放 WSL/Docker 占用的内存。
echo 数据库 volume 已保留。
echo.
pause
