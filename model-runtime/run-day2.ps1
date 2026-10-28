param(
    [string]$PythonPath = (Join-Path $PSScriptRoot ".venv\Scripts\python.exe")
)

$ErrorActionPreference = "Stop"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:LOKY_MAX_CPU_COUNT = "4"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Python environment not found: $PythonPath"
}

& $PythonPath "$PSScriptRoot\day2_validate.py"
if ($LASTEXITCODE -ne 0) {
    throw "Day 2 validation failed with exit code $LASTEXITCODE"
}
