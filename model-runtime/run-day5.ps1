param(
    [string]$FrontendBaseUrl = "http://127.0.0.1:5173",
    [string]$JavaBaseUrl = "http://127.0.0.1:18502",
    [string]$RuntimeBaseUrl = "http://127.0.0.1:8001"
)

$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

& (Join-Path $PSScriptRoot "run-day4.ps1") `
    -FrontendBaseUrl $FrontendBaseUrl `
    -JavaBaseUrl $JavaBaseUrl | Out-Null

& $python (Join-Path $PSScriptRoot "multi_case_validate.py") | Out-Null
$multiCase = Get-Content -LiteralPath (Join-Path $PSScriptRoot "artifacts\multi-case-validation.json") -Raw | ConvertFrom-Json
$health = Invoke-RestMethod -Uri "$RuntimeBaseUrl/health"

$checks = [ordered]@{
    dedicatedVenv = $health.runtimePrefix -eq (Join-Path $PSScriptRoot ".venv")
    python311 = $health.pythonVersion -eq "3.11.9"
    modelHealth = $health.status -eq "ok"
    day4Pass = Test-Path -LiteralPath (Join-Path $PSScriptRoot "artifacts\day4-validation.json")
    multiCasePass = $multiCase.status -eq "PASS" -and $multiCase.cases.Count -eq 3
    startScript = Test-Path -LiteralPath (Join-Path (Split-Path $PSScriptRoot -Parent) "start-all.ps1")
    stopScript = Test-Path -LiteralPath (Join-Path (Split-Path $PSScriptRoot -Parent) "stop-all.ps1")
}
if ($checks.Values -contains $false) {
    throw "One or more Day 5 checks failed"
}

$report = [ordered]@{
    status = "PASS"
    generatedAt = (Get-Date).ToString("o")
    runtimePrefix = $health.runtimePrefix
    pythonVersion = $health.pythonVersion
    checks = $checks
    multiCaseSummary = $multiCase.cases
}
$output = Join-Path $PSScriptRoot "artifacts\day5-validation.json"
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $output -Encoding utf8
$report | ConvertTo-Json -Depth 10
Write-Output "PASS: report written to $output"
