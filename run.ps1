# CV Builder launcher for Windows PowerShell

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Install/update dependencies
Write-Host "Ensuring dependencies are installed..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Run the CLI
if ($Args.Count -eq 0) {
    python -m src.main --help
} else {
    python -m src.main @Args
}
