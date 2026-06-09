@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo 虚拟人物陪伴系统 - 暂时暂停
echo.

echo 正在停止监听 8000 的后端进程...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>nul
)

echo 正在停止监听 9880 的 GPT-SoVITS API 进程（如果存在）...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":9880" ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>nul
)

echo 正在执行 docker compose stop，保留数据库数据...
docker compose stop

echo.
echo 已暂时暂停。
echo PostgreSQL volume、聊天记录、记忆、知识库、人设反馈都会保留。
echo 没有执行 docker compose down。
echo 没有执行 docker compose down -v。
echo 没有执行 wsl --shutdown。
echo.
pause
