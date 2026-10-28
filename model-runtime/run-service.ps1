param(
    [string]$PythonPath = (Join-Path $PSScriptRoot ".venv\Scripts\python.exe"),
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8001
)

$ErrorActionPreference = "Stop"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:LOKY_MAX_CPU_COUNT = "4"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Python environment not found: $PythonPath"
}

& $PythonPath "$PSScriptRoot\service.py" --host $HostAddress --port $Port
if ($LASTEXITCODE -ne 0) {
    throw "Model runtime exited with code $LASTEXITCODE"
}
