@echo off
setlocal
cd /d "%~dp0.."
set "MODE=%~1"
if exist ".venv\Scripts\python.exe" goto dependencies
where py >nul 2>nul
if not errorlevel 1 py -3.12 -m venv .venv
if exist ".venv\Scripts\python.exe" goto dependencies
for /f "delims=" %%P in ('where python 2^>nul ^| findstr /v /i WindowsApps') do (
    "%%P" -m venv .venv
    if exist ".venv\Scripts\python.exe" goto dependencies
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m venv .venv
)
if not exist ".venv\Scripts\python.exe" goto failed
:dependencies
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip --version >nul 2>nul
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m ensurepip --upgrade
    if errorlevel 1 goto failed
)
set "REQ=requirements.txt"
if "%MODE%"=="ui" set "REQ=requirements-ui.txt"
if "%MODE%"=="setup" set "REQ=requirements-providers.txt"
if not exist ".venv\.installed-%MODE%-v1.1.0" (
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "%REQ%"
    if errorlevel 1 goto failed
    type nul > ".venv\.installed-%MODE%-v1.1.0"
)
if "%MODE%"=="ui" (
    ".venv\Scripts\python.exe" -m streamlit run researcher/web_ui.py --global.developmentMode false --browser.gatherUsageStats false
) else if "%MODE%"=="setup" (
    ".venv\Scripts\python.exe" -m researcher.setup
    if errorlevel 1 goto failed
    ".venv\Scripts\python.exe" -m researcher doctor
) else (
    ".venv\Scripts\python.exe" -m researcher demo --offline --no-cache
)
if errorlevel 1 goto failed
if not "%MODE%"=="ui" pause
exit /b 0
:failed
echo Setup or run failed. Python 3.12 is recommended; first installation needs internet.
echo See BASLA_AZ.md. Real research also needs a configured API key.
pause
exit /b 1
