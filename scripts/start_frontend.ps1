# AgentShield - Start Frontend Development Server
# Starts the Vite development server on http://localhost:5173

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $RootDir "frontend"

Set-Location $FrontendDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting AgentShield React Web Console" -ForegroundColor Cyan
Write-Host "  URL: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Backend Target: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

npm run dev
