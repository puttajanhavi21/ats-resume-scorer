@echo off
setlocal
cd /d "%~dp0"
echo ATS Resume Scorer - local learning app
echo.
if exist ".venv\Scripts\python.exe" goto install
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m venv .venv
if errorlevel 1 goto failed
goto install
:use_python
where python >nul 2>nul
if errorlevel 1 goto no_python
python -m venv .venv
if errorlevel 1 goto failed
:install
echo Checking project dependencies. Internet is needed for the first installation.
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo When the server is ready, open http://127.0.0.1:5000 in your browser.
echo Keep this window open. Press Ctrl+C to stop the app.
".venv\Scripts\python.exe" app.py
goto end
:no_python
echo Python was not found. Install Python 3.12 from https://www.python.org/downloads/
echo Enable Add Python to PATH, reopen this file and try again.
goto end
:failed
echo Setup failed. Read the message above and the troubleshooting table in README.md.
:end
pause
