@echo off
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "COMPOSE_FILE=%PROJECT_ROOT%\deploy\docker\docker-compose.yml"

echo.
echo 虚拟人物陪伴系统 - 暂时暂停
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

echo 正在执行 Docker Compose stop，保留数据库数据...
docker compose --project-directory "%PROJECT_ROOT%" -f "%COMPOSE_FILE%" stop

echo.
echo 已暂时暂停。
echo PostgreSQL volume、聊天记录、记忆、知识库、人设反馈都会保留。
echo 没有执行 docker compose down。
echo 没有执行 docker compose down -v。
echo 没有执行 wsl --shutdown。
echo.
pause
