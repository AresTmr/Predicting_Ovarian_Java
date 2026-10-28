param(
    [string]$PythonPath = (Join-Path $PSScriptRoot ".venv\Scripts\python.exe"),
    [string]$BaselineRoot = "C:\Users\24986\Desktop\FJNU\git\Predicting_Ovarian_UI_backup_2026-09-17"
)

$ErrorActionPreference = "Stop"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONIOENCODING = "utf-8"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Python environment not found: $PythonPath"
}
if (-not (Test-Path -LiteralPath $BaselineRoot)) {
    throw "Baseline project not found: $BaselineRoot"
}

& $PythonPath "$PSScriptRoot\day1_validate.py" --baseline-root $BaselineRoot
if ($LASTEXITCODE -ne 0) {
    throw "Day 1 model validation failed with exit code $LASTEXITCODE"
}
