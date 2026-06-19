# Setup hints for Neon PostgreSQL (pgvector) — RolePBP
# Usage: .\scripts\setup_neon.ps1
# Does NOT create Neon resources; guides you and optionally tests the connection.

param(
    [string]$DatabaseUrl = "",
    [switch]$TestOnly
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "=== RolePBP — Neon setup hints ===" -ForegroundColor Cyan
Write-Host ""

if (-not $TestOnly) {
    Write-Host "1. Create project at https://console.neon.tech" -ForegroundColor Yellow
    Write-Host "   - Name: rolepbp"
    Write-Host "   - Region: closest to your players (e.g. Frankfurt)"
    Write-Host ""
    Write-Host "2. Copy the POOLED connection string from Neon Dashboard"
    Write-Host "   postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require"
    Write-Host ""
    Write-Host "3. Convert prefix for asyncpg (Render / local backend):"
    Write-Host "   postgresql+asyncpg://user:pass@ep-xxx...?sslmode=require" -ForegroundColor Green
    Write-Host ""
    Write-Host "4. In Neon SQL Editor, run once:"
    Write-Host "   CREATE EXTENSION IF NOT EXISTS vector;" -ForegroundColor Green
    Write-Host ""
    Write-Host "5. Set DATABASE_URL in:"
    Write-Host "   - Render env vars (backend)"
    Write-Host "   - Local .env (for indexing manuals)"
    Write-Host ""
    Write-Host "6. Index manuals from your PC (PDFs stay local):"
    Write-Host "   cd backend" -ForegroundColor Gray
    Write-Host "   python scripts/index_system_manuals.py --system dnd5e" -ForegroundColor Gray
    Write-Host ""
}

if ($DatabaseUrl) {
    $asyncUrl = $DatabaseUrl -replace "^postgresql://", "postgresql+asyncpg://"
    if ($asyncUrl -notmatch "sslmode=") {
        $asyncUrl += $(if ($asyncUrl -match "\?") { "&" } else { "?" }) + "sslmode=require"
    }
    Write-Host "Converted asyncpg URL:" -ForegroundColor Cyan
    Write-Host $asyncUrl
    Write-Host ""

    $testScript = @"
import asyncio
import sys
sys.path.insert(0, r'$RepoRoot\backend')
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    engine = create_async_engine(r'''$asyncUrl''')
    async with engine.connect() as conn:
        r = await conn.execute(text('SELECT 1'))
        assert r.scalar() == 1
        ext = await conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        row = ext.first()
        if row:
            print('OK: connected + pgvector extension present')
        else:
            print('WARN: connected but vector extension missing — run CREATE EXTENSION vector;')
    await engine.dispose()

asyncio.run(main())
"@
    $tempPy = Join-Path $env:TEMP "rolepbp_neon_test.py"
    Set-Content -Path $tempPy -Value $testScript -Encoding UTF8
    Write-Host "Testing connection..." -ForegroundColor Yellow
    Push-Location (Join-Path $RepoRoot "backend")
    try {
        python $tempPy
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        Pop-Location
        Remove-Item $tempPy -ErrorAction SilentlyContinue
    }
} elseif (-not $TestOnly) {
    Write-Host "Optional: test connection after you have the URL:" -ForegroundColor DarkGray
    Write-Host '  .\scripts\setup_neon.ps1 -DatabaseUrl "postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require"' -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Full deploy guide: docs/DEPLOY_FRIENDS.md" -ForegroundColor Cyan
Write-Host ""
