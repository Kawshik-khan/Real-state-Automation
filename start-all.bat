@echo off
title Grandeur Living - Full Stack Launcher
echo =======================================================
echo Starting Both Backend and Frontend Dev Servers
echo =======================================================
cd /d "%~dp0"
start "Backend - FastAPI" cmd /c "call start-backend.bat"
start "Frontend - Vite" cmd /c "call start-frontend.bat"
echo =======================================================
echo Backend launched on:  http://127.0.0.1:8000
echo Frontend launched on: http://localhost:5173
echo =======================================================
