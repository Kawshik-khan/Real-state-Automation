# Grandeur Living - Frontend Dev Server Launcher
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Starting Frontend (Vite) Dev Server" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan

$WorkspaceRoot = $PSScriptRoot
Set-Location (Join-Path $WorkspaceRoot "frontend")

Write-Host "Launching Vite dev server on http://localhost:5173 ..." -ForegroundColor Cyan
npm run dev
