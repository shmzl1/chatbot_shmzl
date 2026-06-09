@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo 虚拟人物陪伴系统 - 一键启动
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_app.ps1"

echo.
pause
