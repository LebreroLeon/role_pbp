$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Creado .env desde .env.example"
}

Write-Host "Levantando RolePBP (postgres + backend + frontend)..."
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  Backend:  http://localhost:8000/docs"
$lanIp = (
  Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object { $_.IPAddress -match '^(192\.168\.|10\.)' -and $_.PrefixOrigin -ne 'WellKnown' } |
  Select-Object -First 1 -ExpandProperty IPAddress
)
if ($lanIp) {
  Write-Host "  Movil (misma WiFi): http://${lanIp}:5173  (no uses localhost en el telefono)"
}
Write-Host "  Ctrl+C para parar"
Write-Host ""

docker compose up --build