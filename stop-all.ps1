$ErrorActionPreference = "Stop"

foreach ($port in @(5173, 18502, 8001)) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) {
        Stop-Process -Id $listener.OwningProcess -Force
        Write-Output "Stopped port $port (PID $($listener.OwningProcess))"
    }
}
