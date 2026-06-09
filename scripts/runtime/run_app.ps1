$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
$BackendDir = Join-Path $ProjectRoot "backend"
$ComposeFile = Join-Path $ProjectRoot "deploy\docker\docker-compose.yml"
$CondaEnvName = "3-chatbot"
$Url = "http://127.0.0.1:8000/app/"
$PostgresContainerName = "role-chatbot-postgres"

function Fail {
    param([string]$Message)

    Write-Host ""
    Write-Host $Message -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

function Test-PortInUse {
    param([int]$Port)

    $Connection = Get-NetTCPConnection `
        -LocalPort $Port `
        -State Listen `
        -ErrorAction SilentlyContinue

    return $null -ne $Connection
}

function Test-CondaEnvExists {
    param([string]$EnvName)

    $EnvList = conda env list 2>&1
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    foreach ($Line in $EnvList) {
        if ($Line -match "^\s*\*?\s*$([regex]::Escape($EnvName))\s+") {
            return $true
        }
    }

    return $false
}

function Wait-PostgresHealthy {
    param(
        [string]$ContainerName,
        [int]$TimeoutSeconds = 60
    )

    Write-Host "正在等待 PostgreSQL 容器 healthy..."

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $LastStatus = ""

    while ((Get-Date) -lt $Deadline) {
        $Status = docker inspect `
            --format "{{.State.Health.Status}}" `
            $ContainerName `
            2>$null

        if ($LASTEXITCODE -eq 0) {
            $LastStatus = "$Status".Trim()

            if ($LastStatus -eq "healthy") {
                Write-Host "PostgreSQL 容器已 healthy。"
                return
            }

            if ($LastStatus -eq "unhealthy") {
                Fail "PostgreSQL 容器状态为 unhealthy，请检查 Docker 日志。"
            }
        }

        Start-Sleep -Seconds 2
    }

    if (-not $LastStatus) {
        $LastStatus = "unknown"
    }

    Fail "PostgreSQL 容器 $ContainerName 未在 $TimeoutSeconds 秒内变为 healthy，当前状态：$LastStatus"
}

function Test-BackendDependencies {
    Write-Host "正在检查后端依赖..."

    $RequirementsFile = Join-Path $BackendDir "requirements.txt"
    if (-not (Test-Path -LiteralPath $RequirementsFile)) {
        Fail "没有找到后端依赖文件：$RequirementsFile"
    }

    conda run `
        -n $CondaEnvName `
        python -c "import fastapi; import uvicorn; import pydantic"

    if ($LASTEXITCODE -ne 0) {
        Fail "后端依赖检查失败。请执行：cd E:\my_software\chatbot\backend; conda activate 3-chatbot; python -m pip install -r requirements.txt"
    }
}

Write-Host ""
Write-Host "虚拟人物陪伴系统 - 一键启动" -ForegroundColor Cyan
Write-Host ""
Write-Host "项目目录: $ProjectRoot"
Write-Host "后端目录: $BackendDir"
Write-Host "Compose 文件: $ComposeFile"
Write-Host "Conda 环境: $CondaEnvName"
Write-Host ""

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Fail "没有找到 docker 命令。请确认 Docker Desktop 已安装并正在运行。"
}

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Fail "没有找到 conda 命令。请确认 Miniconda/Anaconda 已安装，并且 conda 在 PATH 中可用。"
}

if (-not (Test-CondaEnvExists -EnvName $CondaEnvName)) {
    Fail "没有找到 conda 环境：$CondaEnvName"
}

if (-not (Test-Path -LiteralPath $BackendDir)) {
    Fail "没有找到后端目录：$BackendDir"
}

if (-not (Test-Path -LiteralPath $ComposeFile)) {
    Fail "没有找到 Docker Compose 文件：$ComposeFile"
}

if (Test-PortInUse -Port 8000) {
    Write-Host "端口 8000 已经被占用，可能后端已经在运行。" -ForegroundColor Yellow
    Write-Host "不会重复启动多个后端。"
    Write-Host "正在打开现有页面：$Url"
    Start-Process $Url
    exit 0
}

Write-Host "正在启动 Docker 数据库..."
docker compose --project-directory "$ProjectRoot" -f "$ComposeFile" up -d postgres adminer

if ($LASTEXITCODE -ne 0) {
    Fail "docker compose --project-directory `"$ProjectRoot`" -f `"$ComposeFile`" up -d postgres adminer 执行失败。请确认 Docker Desktop 正在运行。"
}

Wait-PostgresHealthy -ContainerName $PostgresContainerName
Test-BackendDependencies

Write-Host ""
Write-Host "提示：GPT-SoVITS 语音 API 不会自动启动。"
Write-Host "如需语音，请单独启动 9880 API。不启动语音时可以继续文字聊天。"
Write-Host ""

Write-Host "正在打开网页：$Url"
Start-Process $Url

Write-Host ""
Write-Host "正在打开新的 PowerShell 窗口启动 FastAPI 后端。"
Write-Host "本脚本不会执行 docker compose down 或 docker compose down -v。"
Write-Host ""

$BackendCommand = @"
Set-Location -LiteralPath "$BackendDir"
conda run --no-capture-output -n $CondaEnvName python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
Read-Host "后端进程已退出，按 Enter 关闭窗口"
"@

Start-Process powershell `
    -WindowStyle Normal `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $BackendCommand
