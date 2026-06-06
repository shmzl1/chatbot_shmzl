@echo off
chcp 65001 >nul

echo 正在停止 chatbot 后端 8000...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"

echo 正在停止 GPT-SoVITS API 9880...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 9880 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"

echo 正在停止 Docker 数据库容器，但保留数据...
cd /d E:\my_software\chatbot
docker compose stop

echo.
echo 已暂停完成。
echo 数据库数据、聊天记录、记忆都会保留。
echo.
pause