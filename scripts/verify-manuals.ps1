#Requires -Version 5.1
param(
  [string]$ManualsDir = (Join-Path $PSScriptRoot "..\data\manuals\dnd5e")
)

$ManualsDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ManualsDir)

if (-not (Test-Path -LiteralPath $ManualsDir)) {
  Write-Error "Manuals directory not found: $ManualsDir"
  exit 2
}

$pdfs = Get-ChildItem -LiteralPath $ManualsDir -File -Filter "*.pdf"
$patterns = @(
  @{ Label = "Player Handbook"; Regex = "Manual del Jugador" },
  @{ Label = "DM Guide"; Regex = "Gu[ií]a del Dungeon Master" },
  @{ Label = "Monster Manual"; Regex = "Manual de Monstruos" }
)

Write-Host "Manuals dir: $ManualsDir"
Write-Host "PDF count: $($pdfs.Count)"
$sum = ($pdfs | Measure-Object -Property Length -Sum).Sum
if ($sum) { Write-Host ("Total size: {0:N1} MB" -f ($sum / 1MB)) }

$missing = @()
foreach ($p in $patterns) {
  $hit = $pdfs | Where-Object { $_.Name -match $p.Regex } | Select-Object -First 1
  if ($hit) {
    Write-Host "[OK] $($p.Label): $($hit.Name)"
  } else {
    Write-Host "[MISSING] $($p.Label)"
    $missing += $p.Label
  }
}

if ($missing.Count -gt 0) {
  Write-Host ""
  Write-Host "See docs/MANUALS_MOBILE.md for sync instructions."
  exit 1
}

Write-Host ""
Write-Host "Core manuals present."
exit 0
