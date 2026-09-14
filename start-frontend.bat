@echo off
title Grandeur Living - Frontend Dev Server
echo =======================================================
echo Starting Frontend (Vite) Dev Server
echo =======================================================
cd /d "%~dp0frontend"
echo Running npm run dev ...
npm run dev
pause
