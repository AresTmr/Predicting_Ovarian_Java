param(
    [string]$FrontendBaseUrl = "http://127.0.0.1:5173",
    [string]$JavaBaseUrl = "http://127.0.0.1:18502"
)

$ErrorActionPreference = "Stop"
$case = Get-Content -LiteralPath (Join-Path $PSScriptRoot "fixtures\representative_case.json") -Raw | ConvertFrom-Json
$payload = @{
    patient = $case.patient
    records = $case.monitoring_records
} | ConvertTo-Json -Depth 30

$pages = @(
    "PatientEntry",
    "MonitoringResult",
    "DecisionCurve",
    "Recommendation"
)
$pageChecks = [ordered]@{}
foreach ($page in $pages) {
    $response = Invoke-WebRequest -UseBasicParsing "$FrontendBaseUrl/src/views/$page.vue"
    $pageChecks[$page] = $response.StatusCode -eq 200
}

$run = Invoke-RestMethod `
    -Method Post `
    -Uri "$JavaBaseUrl/api/v1/recommendation-runs" `
    -ContentType "application/json; charset=utf-8" `
    -Body $payload `
    -TimeoutSec 60

$loaded = Invoke-RestMethod -Uri "$JavaBaseUrl/api/v1/recommendation-runs/$($run.runId)"
$checks = [ordered]@{
    patientPage = $pageChecks.PatientEntry
    monitoringPage = $pageChecks.MonitoringResult
    decisionPage = $pageChecks.DecisionCurve
    recommendationPage = $pageChecks.Recommendation
    runCreated = $run.status -eq "OK"
    runPersisted = $loaded.runId -eq $run.runId
    fshCategory = $loaded.result.summary.fsh.category -eq ">160"
    fshDose = [double]$loaded.result.summary.fsh.actualDose -eq 200.0
    oocytes = [double]$loaded.result.summary.oocytes -eq 12.0
    candidates = $loaded.result.candidates.Count -eq 8
    fshCurveAnchor = ($loaded.result.curves.fsh | Where-Object { $_.recommended }).dose -eq 200.0
    knn = $loaded.result.explanations.knn.status -eq "OK"
    doseExplanation = [double]$loaded.result.explanations.dose.fsh.currentProbability -gt 0.89
}
if ($checks.Values -contains $false) {
    throw "One or more Day 4 checks failed"
}

$report = [ordered]@{
    status = "PASS"
    generatedAt = (Get-Date).ToString("o")
    runId = $run.runId
    checks = $checks
    summary = [ordered]@{
        fsh = $loaded.result.summary.fsh.category
        fshActualDose = $loaded.result.summary.fsh.actualDose
        lhDose = $loaded.result.summary.lh.actualDose
        hmgDose = $loaded.result.summary.hmg.actualDose
        oocytes = $loaded.result.summary.oocytes
        ohssRiskPercent = $loaded.result.summary.ohssRiskPercent
        candidateCount = $loaded.result.candidates.Count
        knnFshCaseCount = $loaded.result.explanations.knn.items.fsh[0].case_count
    }
}

$output = Join-Path $PSScriptRoot "artifacts\day4-validation.json"
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $output -Encoding utf8
$report | ConvertTo-Json -Depth 10
Write-Output "PASS: report written to $output"
