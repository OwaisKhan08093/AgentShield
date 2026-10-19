# AgentShield - Start Backend Server
# Starts the FastAPI application on http://127.0.0.1:8000

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Split-Path -Parent $ScriptDir

Set-Location $RootDir
$VenvPython = Join-Path $RootDir "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] Virtual environment python not found at $VenvPython" -ForegroundColor Red
    Write-Host "Please set up the backend virtual environment: python -m venv backend\.venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting AgentShield FastAPI Backend" -ForegroundColor Cyan
Write-Host "  URL: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  Interactive Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

& $VenvPython -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
