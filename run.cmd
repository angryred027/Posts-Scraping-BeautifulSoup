@echo off

REM ===== ACTIVATE VENV =====
call .\venv\Scripts\activate

REM ===== RUN SCRIPT =====
python main.py

echo.
echo ===== SCRIPT FINISHED =====
echo Exit code: %ERRORLEVEL%
echo.
echo Window will close in 60 seconds...
timeout /t 60 /nobreak