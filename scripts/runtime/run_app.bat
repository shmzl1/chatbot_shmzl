@echo off
chcp 65001 >nul
echo 正在启动虚拟人物陪伴系统...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_app.ps1"
pause
