$ErrorActionPreference = "Stop"
$env:Path = "C:\Program Files\Git\cmd;C:\Program Files\nodejs;C:\Users\lebre\AppData\Local\Programs\Python\Python312;C:\Users\lebre\AppData\Local\Programs\Python\Python312\Scripts;" + $env:Path

Set-Location $PSScriptRoot\..\backend
if (-not (Test-Path ".venv")) {
  python -m venv .venv
  .\.venv\Scripts\pip install -r requirements.txt
}

.\.venv\Scripts\python -m app.core.migrate
Write-Host "Migrations applied."
