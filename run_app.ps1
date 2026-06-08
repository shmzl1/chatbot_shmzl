$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot "backend"
$CondaEnvName = "3-chatbot"
$Url = "http://127.0.0.1:8000/app/"

function Fail($Message) {
    Write-Host ""
    Write-Host $Message -ForegroundColor Yellow
    Write-Host ""
    Read-Host "按 Enter 退出"
    exit 1
}

function Test-PortInUse($Port) {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $connection
}

Write-Host ""
Write-Host "虚拟人物陪伴系统" -ForegroundColor Cyan
Write-Host "项目目录: $ProjectRoot"
Write-Host "后端目录: $BackendDir"
Write-Host "Conda 环境: $CondaEnvName"
Write-Host ""

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Fail "没有找到 docker 命令。请确认 Docker Desktop 已安装并正在运行。"
}

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Fail "没有找到 conda 命令。请确认 Miniconda/Anaconda 已安装，并且 conda 在 PATH 中可用。"
}

if (Test-PortInUse 8000) {
    Write-Host "端口 8000 已经被占用，可能后端已经在运行。" -ForegroundColor Yellow
    Write-Host "不会重复启动多个后端。正在打开现有页面：$Url"
    Start-Process $Url
    Read-Host "按 Enter 退出"
    exit 0
}

Write-Host "启动 Docker 数据库..."
Set-Location -LiteralPath $ProjectRoot
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Fail "docker compose up -d 执行失败。请确认 Docker Desktop 正在运行。"
}

Write-Host ""
Write-Host "提示：GPT-SoVITS 语音 API 不会自动启动。"
Write-Host "如需语音，请单独启动 9880 API。不开语音时可继续文字聊天。"
Write-Host ""

$BackendCommand = @"
`$ErrorActionPreference = 'Stop'
chcp 65001 >`$null
Set-Location -LiteralPath '$BackendDir'
Write-Host '虚拟人物陪伴系统后端'
Write-Host '正在激活 conda 环境 $CondaEnvName...'
conda shell.powershell hook | Out-String | Invoke-Expression
conda activate $CondaEnvName
if (`$LASTEXITCODE -ne 0) { throw 'conda activate $CondaEnvName 失败' }
Write-Host '安装/检查 Python 依赖...'
python -m pip install -r requirements.txt
if (`$LASTEXITCODE -ne 0) { throw '依赖安装失败' }
Write-Host '启动 FastAPI: http://127.0.0.1:8000/app/'
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
"@

Write-Host "正在新 PowerShell 窗口启动后端..."
Start-Process powershell -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-NoExit",
    "-Command", $BackendCommand
)

Start-Sleep -Seconds 2
Write-Host "正在打开网页：$Url"
Start-Process $Url

Write-Host ""
Write-Host "启动命令已发出。后端日志请看新打开的 PowerShell 窗口。"
Write-Host "本脚本不会执行 docker compose down 或 docker compose down -v。"
