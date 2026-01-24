@echo off
REM CV Builder launcher for Windows Command Prompt

setlocal enabledelayedexpansion

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call "venv\Scripts\activate.bat"

REM Install/update dependencies
echo Ensuring dependencies are installed...
pip install -q -r requirements.txt

REM Run the CLI
if "%1"=="" (
    python -m src.main --help
) else (
    python -m src.main %*
)
