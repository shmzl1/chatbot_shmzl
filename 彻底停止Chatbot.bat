@echo off
chcp 65001 >nul

echo 正在停止 chatbot 后端 8000...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"

echo 正在停止 GPT-SoVITS API 9880...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 9880 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"

echo 正在停止 Docker 容器...
cd /d E:\my_software\chatbot
docker compose stop

echo 正在关闭 WSL，释放 Docker 占用内存...
wsl --shutdown

echo.
echo 已彻底释放内存。
echo 注意：这会关闭所有 WSL，包括 Docker Desktop 后端和其他 WSL 终端。
echo 数据库 volume 不会被删除。
echo.
pause