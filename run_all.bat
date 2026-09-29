@echo off
title RECALL-X Launcher
echo ========================================================
echo RECALL-X -- Launching Backend and Frontend
echo ========================================================
cd /d "%~dp0"
echo Starting Backend in a new window...
start "RECALL-X Backend" cmd /k "call run_backend.bat"
echo Starting Frontend in a new window...
start "RECALL-X Frontend" cmd /k "call run_frontend.bat"
echo Both servers are starting up:
echo - Backend: http://127.0.0.1:8000
echo - Frontend: http://localhost:3000
echo.
echo You can close this launcher window once both windows appear.
pause
