# Grandeur Living - Real Estate Automation Backend Launcher
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Starting FastAPI Backend for AI Evaluation Engine" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan

$WorkspaceRoot = $PSScriptRoot
Set-Location $WorkspaceRoot

$VenvPython1 = Join-Path $WorkspaceRoot "backend\.venv\Scripts\python.exe"
$VenvPython2 = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython1) {
    Write-Host "Virtual environment detected: $VenvPython1" -ForegroundColor Green
    $PythonExe = $VenvPython1
} elseif (Test-Path $VenvPython2) {
    Write-Host "Virtual environment detected: $VenvPython2" -ForegroundColor Green
    $PythonExe = $VenvPython2
} else {
    Write-Host "[WARNING] .venv not found; using system 'python'" -ForegroundColor Yellow
    $PythonExe = "python"
}

$env:PYTHONPATH = Join-Path $WorkspaceRoot "backend"
Write-Host "PYTHONPATH set to: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "Launching uvicorn on http://127.0.0.1:8000 ..." -ForegroundColor Cyan

& $PythonExe -m uvicorn app.main:app --app-dir "$env:PYTHONPATH" --reload-dir "$env:PYTHONPATH" --host 127.0.0.1 --port 8000 --reload
