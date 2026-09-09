@echo off
rem Backend dev server (http://localhost:8000). Kept open by dev-start.bat.
cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
