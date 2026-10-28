param(
    [string]$JavaHome = $env:JAVA_HOME
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$logDir = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if ([string]::IsNullOrWhiteSpace($JavaHome)) {
    $JavaHome = "D:\Java\JDK"
}

$python = Join-Path $root "model-runtime\.venv\Scripts\python.exe"
$modelService = Join-Path $root "model-runtime\service.py"
$java = Join-Path $JavaHome "bin\java.exe"
$jar = Join-Path $root "target\predicting-ovarian.jar"
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source

foreach ($required in @($python, $modelService, $java, $jar)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required file not found: $required"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $root "frontend\node_modules"))) {
    throw "frontend/node_modules not found. Run 'npm install' in frontend first."
}

if (-not (Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process `
        -FilePath $python `
        -ArgumentList @($modelService, "--host", "127.0.0.1", "--port", "8001") `
        -WorkingDirectory (Join-Path $root "model-runtime") `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "model-runtime.out.log") `
        -RedirectStandardError (Join-Path $logDir "model-runtime.err.log")
}

if (-not (Get-NetTCPConnection -LocalPort 18502 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process `
        -FilePath $java `
        -ArgumentList @("-jar", $jar) `
        -WorkingDirectory $root `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "java.out.log") `
        -RedirectStandardError (Join-Path $logDir "java.err.log")
}

if (-not (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process `
        -FilePath $npm `
        -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "5173") `
        -WorkingDirectory (Join-Path $root "frontend") `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "vite.out.log") `
        -RedirectStandardError (Join-Path $logDir "vite.err.log")
}

$deadline = (Get-Date).AddSeconds(30)
do {
    Start-Sleep -Milliseconds 500
    $modelReady = [bool](Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue)
    $javaReady = [bool](Get-NetTCPConnection -LocalPort 18502 -State Listen -ErrorAction SilentlyContinue)
    $viteReady = [bool](Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)
} while ((!$modelReady -or !$javaReady -or !$viteReady) -and (Get-Date) -lt $deadline)

if (-not $modelReady -or -not $javaReady -or -not $viteReady) {
    throw "Services did not become ready. Check logs under $logDir"
}

Invoke-RestMethod -Uri "http://127.0.0.1:18502/api/v1/recommendation-runs/runtime/health" | Out-Null
Write-Output "Model runtime: http://127.0.0.1:8001"
Write-Output "Java backend:  http://127.0.0.1:18502"
Write-Output "Vue frontend:  http://127.0.0.1:5173"
