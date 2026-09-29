@echo off
title RECALL-X Backend (Port 8000)
echo ========================================================
echo RECALL-X -- Operational Experience Memory Backend
echo ========================================================
cd /d "%~dp0"
echo Starting FastAPI server at http://127.0.0.1:8000 ...
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
