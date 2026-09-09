@echo off
rem Frontend dev server (http://localhost:5173). Kept open by dev-start.bat.
cd /d "%~dp0frontend"
call npm run dev
