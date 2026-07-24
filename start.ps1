Param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

# --- Headless mode ---
if ($Headless -and ($Host.Name -ne 'ConsoleHost' -or -not (Get-Variable -Name "NoRelaunch" -ErrorAction SilentlyContinue))) {
    $argList = @("-File", $PSCommandPath, "-NoRelaunch")
    if ($BackendOnly) { $argList += "-BackendOnly" }
    $argList += "-NoBrowser"
    Start-Process pwsh.exe -ArgumentList $argList -WindowStyle Hidden
    exit
}

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$WebPort = 10822
$BackendPort = 10823

# -- Require-Command: auto-install missing tools via winget --
function Require-Command($Name, $WingetId) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Host "Installing $Name via winget..." -ForegroundColor Yellow
        winget install --id $WingetId -e --accept-source-agreements --accept-package-agreements 2>$null
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
        if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
            Write-Host "Failed to install $Name. Install manually." -ForegroundColor Red
            exit 1
        }
    }
}

Require-Command "uv" "astral-sh.uv"
Require-Command "bun" "Oven-sh.Bun"

Write-Host "=== netatmo-weather-mcp ===" -ForegroundColor Cyan

# -- Kill port zombies --
foreach ($p in @($WebPort, $BackendPort)) {
    Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

# -- Python deps --
if ($env:SKIP_SYNC -ne "1") {
    Write-Host "[1/3] uv sync..." -ForegroundColor Cyan
    Set-Location $RepoRoot
    uv sync
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# -- Start backend --
Write-Host "[2/3] Starting backend (port $BackendPort)..." -ForegroundColor Cyan
$backendProc = Start-Process uv -ArgumentList "run", "uvicorn", "netatmo_weather_mcp.web_app:app", "--host", "127.0.0.1", "--port", "$BackendPort" `
    -WorkingDirectory $RepoRoot -PassThru -NoNewWindow

# Health poll
Write-Host "  Waiting for backend..." -ForegroundColor Gray
$ok = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch {}
    Start-Sleep 1
}
if (-not $ok) { Write-Host "  Backend failed to start within 60s" -ForegroundColor Red; exit 1 }
Write-Host "  Backend ready" -ForegroundColor Green

if ($BackendOnly) { Write-Host "Backend-only mode."; Wait-Process -Id $backendProc.Id; exit }

# -- Start frontend --
Write-Host "[3/3] Starting frontend..." -ForegroundColor Cyan
Set-Location (Join-Path $RepoRoot "web_sota")
if (-not (Test-Path "node_modules")) { bun install }
$null = Start-Process bun -ArgumentList "run", "vite", "--port", "$WebPort" -WorkingDirectory (Join-Path $RepoRoot "web_sota")

if (-not $NoBrowser) {
    Start-Sleep 3
    Start-Process "http://localhost:$WebPort"
}

Write-Host "Frontend: http://localhost:$WebPort" -ForegroundColor Green

# Keep alive
try {
    Wait-Process -Id $backendProc.Id
} finally {
    if ($backendProc -and -not $backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    }
}
