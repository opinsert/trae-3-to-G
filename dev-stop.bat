@echo off
rem One-click stop: close the two dev cmd windows and free ports 8000/5175

echo Stopping dev servers...

taskkill /FI "WINDOWTITLE eq GCode-Backend-8000*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq GCode-Frontend-5175*" /T /F >nul 2>&1

rem Fallback: kill whatever listens on the two ports
for %%P in (8000 5175) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
    taskkill /PID %%A /T /F >nul 2>&1
  )
)

echo Done. Ports 8000 and 5175 should be free now.
timeout /t 2 /nobreak >nul
