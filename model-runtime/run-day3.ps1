param(
    [string]$JavaBaseUrl = "http://127.0.0.1:18502",
    [string]$RuntimeBaseUrl = "http://127.0.0.1:8001"
)

$ErrorActionPreference = "Stop"
$fixture = Join-Path $PSScriptRoot "fixtures\representative_case.json"
$case = Get-Content -LiteralPath $fixture -Raw | ConvertFrom-Json
$payload = @{
    patient = $case.patient
    records = $case.monitoring_records
} | ConvertTo-Json -Depth 30

$health = Invoke-RestMethod -Uri "$JavaBaseUrl/api/v1/recommendation-runs/runtime/health"
if ($health.status -ne "ok") {
    throw "Model runtime health check failed"
}

$created = Invoke-RestMethod `
    -Method Post `
    -Uri "$JavaBaseUrl/api/v1/recommendation-runs" `
    -ContentType "application/json; charset=utf-8" `
    -Body $payload `
    -TimeoutSec 60

if ($created.status -ne "OK" -or [string]::IsNullOrWhiteSpace($created.runId)) {
    throw "Analysis run creation failed"
}

$loaded = Invoke-RestMethod -Uri "$JavaBaseUrl/api/v1/recommendation-runs/$($created.runId)"
if ($loaded.status -ne "OK") {
    throw "Persisted analysis run cannot be loaded"
}

$checks = [ordered]@{
    health = $health.status -eq "ok"
    runCreated = -not [string]::IsNullOrWhiteSpace($created.runId)
    runPersisted = $loaded.runId -eq $created.runId
    statusOk = $loaded.status -eq "OK"
    fshDose200 = [double]$loaded.result.summary.fsh.actualDose -eq 200.0
    fshCategory = $loaded.result.summary.fsh.category -eq ">160"
    oocytes12 = [double]$loaded.result.summary.oocytes -eq 12.0
    ohss105 = [double]$loaded.result.summary.ohssRiskPercent -eq 1.05
    eightCandidates = $loaded.result.candidates.Count -eq 8
    fshCurveAnchor = ($loaded.result.curves.fsh | Where-Object { $_.recommended }).dose -eq 200.0
    knnAvailable = $loaded.result.explanations.knn.status -eq "OK"
    knnFshCases = $loaded.result.explanations.knn.items.fsh[0].case_count -eq 22
    doseExplanation = [double]$loaded.result.explanations.dose.fsh.currentProbability -gt 0.89
}

if ($checks.Values -contains $false) {
    throw "One or more Day 3 checks failed"
}

$report = [ordered]@{
    status = "PASS"
    generatedAt = (Get-Date).ToString("o")
    javaBaseUrl = $JavaBaseUrl
    runtimeBaseUrl = $RuntimeBaseUrl
    runId = $created.runId
    checks = $checks
    summary = [ordered]@{
        fshDose = $loaded.result.summary.fsh.actualDose
        fshCategory = $loaded.result.summary.fsh.category
        lhDose = $loaded.result.summary.lh.actualDose
        hmgDose = $loaded.result.summary.hmg.actualDose
        oocytes = $loaded.result.summary.oocytes
        ohssRiskPercent = $loaded.result.summary.ohssRiskPercent
        candidateCount = $loaded.result.candidates.Count
        knnFshCaseCount = $loaded.result.explanations.knn.items.fsh[0].case_count
    }
    failurePolicy = "Model runtime unavailable returns HTTP 503; no mock clinical result"
}

$output = Join-Path $PSScriptRoot "artifacts\day3-validation.json"
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $output -Encoding utf8
$report | ConvertTo-Json -Depth 10
Write-Output "PASS: report written to $output"
