@echo off
rem One-click start: backend API (:8000) + frontend web (:5175)
cd /d "%~dp0"

if not exist "backend\app\main.py" (
  echo ERROR: backend\app\main.py not found. Run this file from the project root.
  pause
  exit /b 1
)

echo Starting backend API  -> http://localhost:8000
start "GCode-Backend-8000" cmd /k "call dev-backend.bat"

timeout /t 1 /nobreak >nul

echo Starting frontend web -> http://localhost:5175
start "GCode-Frontend-5175" cmd /k "call dev-frontend.bat"

echo.
echo ============================================================
echo  Services are starting, please wait a few seconds.
echo.
echo  Frontend (open in browser):  http://localhost:5175
echo  Backend  API docs:           http://localhost:8000/docs
echo.
echo  Copy the frontend address into your browser. Keep the two
echo  cmd windows open. To stop later, run dev-stop.bat
echo ============================================================
echo.
