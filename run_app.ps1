$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot "backend"
$CondaEnvName = "3-chatbot"
$Url = "http://127.0.0.1:8000/app/"
$ComposeFile = Join-Path $ProjectRoot "docker-compose.yml"

function Find-CondaCommand {
    $conda = Get-Command conda -ErrorAction SilentlyContinue
    if ($conda) {
        return $conda.Source
    }

    $candidates = @(
        "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
        "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
        "$env:LOCALAPPDATA\miniconda3\Scripts\conda.exe",
        "$env:LOCALAPPDATA\anaconda3\Scripts\conda.exe",
        "C:\ProgramData\miniconda3\Scripts\conda.exe",
        "C:\ProgramData\anaconda3\Scripts\conda.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

Write-Host ""
Write-Host "Local Role Voice Chatbot" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot"
Write-Host "Backend: $BackendDir"
Write-Host "Conda env: $CondaEnvName"
Write-Host ""

$Docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $Docker) {
    Write-Host "没有找到 docker。请确认 Docker Desktop 已安装并启动。" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

Write-Host "Starting PostgreSQL with Docker Compose..."
& docker compose -f $ComposeFile up -d postgres adminer
if ($LASTEXITCODE -ne 0) {
    Write-Host "PostgreSQL 启动失败。请确认 Docker Desktop 正在运行，且 5432 端口没有被占用。" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

Write-Host "Waiting for PostgreSQL..."
for ($i = 0; $i -lt 30; $i++) {
    $Health = docker inspect -f "{{.State.Health.Status}}" role-chatbot-postgres 2>$null
    if ($Health -eq "healthy") {
        break
    }
    Start-Sleep -Seconds 1
}

if ($Health -ne "healthy") {
    Write-Host "PostgreSQL 还没 ready。可以等 Docker Desktop 里容器变 healthy 后再运行脚本。" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

$Conda = Find-CondaCommand
if (-not $Conda) {
    Write-Host "没有找到 conda。请确认 Miniconda 已安装，并且 conda 可用。" -ForegroundColor Yellow
    Write-Host "你也可以手动运行：conda activate $CondaEnvName，然后在 backend 里启动 uvicorn。"
    Read-Host "按 Enter 退出"
    exit 1
}

Write-Host "Conda: $Conda"

& $Conda run -n $CondaEnvName python -c "import fastapi, uvicorn, openai, dotenv, psycopg" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "conda 环境 $CondaEnvName 不存在，或依赖还没装好。" -ForegroundColor Yellow
    Write-Host "请先手动运行：" -ForegroundColor Yellow
    Write-Host "conda activate $CondaEnvName" -ForegroundColor Yellow
    Write-Host "pip install -r `"$ProjectRoot\requirements.txt`"" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

Write-Host "Opening $Url"
Start-Process $Url
Write-Host "Server is running. Press Ctrl+C to stop."
Write-Host ""

Set-Location -LiteralPath $BackendDir
& $Conda run --no-capture-output -n $CondaEnvName python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
