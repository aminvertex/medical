@echo off
setlocal
if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run setup_windows.bat first.
  exit /b 1
)
set PORT=%1
if "%PORT%"=="" set PORT=8000
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:%PORT%
