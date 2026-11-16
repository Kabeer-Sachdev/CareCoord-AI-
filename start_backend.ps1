$ErrorActionPreference = "Continue"
while ($true) {
    Write-Host "[CareCoord] Starting FastAPI Backend on 0.0.0.0:8000..."
    python -u -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
    Write-Host "[CareCoord] Backend process exited, restarting in 1 second..."
    Start-Sleep -Seconds 1
}
