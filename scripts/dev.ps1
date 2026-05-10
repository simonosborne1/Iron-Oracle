$root = Split-Path $PSScriptRoot -Parent

Write-Host "Starting Iron Oracle..."
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  API docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop."

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\backend'; .\.venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000"
)

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\frontend'; npm run dev"
)
