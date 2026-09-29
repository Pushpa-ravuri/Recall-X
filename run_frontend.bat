@echo off
title RECALL-X Frontend (Port 3000)
echo ========================================================
echo RECALL-X -- Operational Experience Memory Frontend
echo ========================================================
cd /d "%~dp0frontend"
echo Starting Next.js frontend at http://localhost:3000 ...
npm run dev
pause
