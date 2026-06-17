# D&D 5e End-to-End Verification (Local)

**Date:** 2026-06-17  
**Project:** `C:\Users\lebre\Projects\role_pbp`  
**Scope:** Backend rules/combat tests, frontend build, Docker config/runtime, optional API smoke.

## Summary

| Check | Result | Notes |
|-------|--------|-------|
| `pytest tests/test_combat.py tests/test_rules_dnd5e.py` | **PASS** | 29/29 in ~1.4s |
| `npm run build` (frontend) | **PASS** | `tsc -b && vite build` OK; PWA assets generated |
| `docker compose config` | **PASS** | Valid stack: postgres, backend:8000, frontend:5173 |
| Docker runtime (backend API) | **FAIL** | Crash-loop: circular import `scenes` â†” `master` (pgvector fixed) |
| HTTP smoke (register ? campaign ? sheet ? roll) | **NOT RUN** | Backend not serving on :8000 |
| Code fixes in repo | **None** | No source changes required for D&D logic |

**Overall:** Unit/build layer **passes**; `pgvector` image rebuild **passes**; full stack E2E **blocked** until circular import in `app.services.scenes` / `app.services.master` is fixed.

---

## 1. Backend tests

```powershell
Set-Location C:\Users\lebre\Projects\role_pbp\backend
pip install -r requirements.txt
pytest tests/test_combat.py tests/test_rules_dnd5e.py -v
```

**Result:** 29 passed, 0 failed (Python 3.12.10, pytest 9.1.0).

Coverage highlights:
- Combat parser (ES/EN), plugin gate (`dnd5e` only), entity resolution, permissions, attack execution
- D&D 5e schema, modifiers, skill/save/attack/damage rolls, dice delegation, combat damage application

---

## 2. Frontend build

```powershell
Set-Location C:\Users\lebre\Projects\role_pbp\frontend
npm run build
```

**Result:** Success (Vite production build, ~488 kB JS bundle). Minor npm warning: unknown env config `devdir` (non-blocking).

D&D UI paths present: `gameSystems.ts` (`dnd5e`), `Dnd5eSheetForm.tsx`, default wizard system `dnd5e`.

---

## 3. Docker

**Compose file:** `docker-compose.yml` ï¿½ Postgres (pgvector image), backend with bind-mounted `app/`, frontend dev on 5173.

**`docker compose config`:** Renders valid merged config (uses project `.env` for API keys and app settings).

**Runtime (at verification time):**

| Container | Status |
|-----------|--------|
| `rolepbp-postgres` | Healthy |
| `rolepbp-frontend` | Serving HTML on http://localhost:5173 |
| `rolepbp-backend` | **Broken** ï¿½ `ModuleNotFoundError: No module named 'pgvector'` |

**Root cause:** `backend/requirements.txt` already includes `pgvector>=0.3.6`, but the running backend image was built **without** that package (`pip show pgvector` inside container: not found). Image/container created 2026-06-17; requirements likely updated after last `docker compose build`.

**Remediation (user):**

```powershell
Set-Location C:\Users\lebre\Projects\role_pbp
docker compose build backend
docker compose up -d backend
docker logs rolepbp-backend --tail 20
curl.exe -s http://127.0.0.1:8000/api/v1/health
```

Expected health: `{"status":"ok","service":"rolepbp-api"}`.


### Backend image rebuild (2026-06-17 follow-up)

Commands run:

```powershell
Set-Location C:\Users\lebre\Projects\role_pbp
docker compose build backend --no-cache
docker compose up -d backend postgres
docker compose run --rm backend alembic upgrade head
curl.exe -s http://127.0.0.1:8000/api/v1/health
```

| Step | Result | Notes |
|------|--------|-------|
| `docker compose build backend --no-cache` | **PASS** | `pgvector-0.4.2` installed in image |
| `docker compose up -d backend postgres` | **PASS** | Postgres healthy; backend recreated |
| `alembic upgrade head` (one-off container) | **PASS** | PostgreSQL context OK |
| `import pgvector` in backend image | **PASS** | Module loads (no `ModuleNotFoundError`) |
| Backend uvicorn / `:8000` health | **PASS** | Fixed circular import (2026-06-17): lazy `load_scene_state` import in `master.py`; `curl /api/v1/health` → `{"status":"ok","service":"rolepbp-api"}` |
| HTTP smoke (section 4) | **NOT RUN** | Backend healthy; section 4 checklist still manual |

**Note:** Host ? Postgres on `127.0.0.1:5432` accepts TCP but `asyncpg` from Windows host failed during this session (`ConnectionDoesNotExistError`). Prefer API smoke through Docker backend after rebuild, or troubleshoot Docker Desktop port forwarding if running uvicorn on the host.

---

## 4. Manual API smoke checklist (D&D 5e)

Base URL: `http://127.0.0.1:8000/api/v1`

**Important:** Sheet upsert/roll require **PLAYER** role. Campaign creator is **MASTER** only ï¿½ use two users or add a player member.

### 4.1 Register master

```powershell
$base = "http://127.0.0.1:8000/api/v1"
$reg = @{
  email = "master-dnd-verify@example.com"
  password = "TestPass123!"
  display_name = "DM Verify"
} | ConvertTo-Json
$auth = Invoke-RestMethod -Method Post -Uri "$base/auth/register" -Body $reg -ContentType "application/json"
$masterToken = $auth.access_token
```

### 4.2 Create D&D 5e campaign

```powershell
$camp = @{ name = "D&D Verify"; tone = "heroic"; game_system = "dnd5e" } | ConvertTo-Json
$headers = @{ Authorization = "Bearer $masterToken" }
$campaign = Invoke-RestMethod -Method Post -Uri "$base/campaigns" -Body $camp -ContentType "application/json" -Headers $headers
$campaignId = $campaign.id
```

### 4.3 Register player + add to campaign (master)

```powershell
$reg2 = @{
  email = "player-dnd-verify@example.com"
  password = "TestPass123!"
  display_name = "PC Verify"
} | ConvertTo-Json
$playerAuth = Invoke-RestMethod -Method Post -Uri "$base/auth/register" -Body $reg2 -ContentType "application/json"
# Master adds player by email (see POST /campaigns/{id}/members in API docs)
$member = @{ email = "player-dnd-verify@example.com"; role = "PLAYER" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/campaigns/$campaignId/members" -Body $member -ContentType "application/json" -Headers $headers
$playerToken = $playerAuth.access_token
$playerHeaders = @{ Authorization = "Bearer $playerToken" }
```

### 4.4 Upsert D&D 5e sheet (player)

Use `PUT /campaigns/{campaign_id}/my-sheet` with `CharacterSheetUpsert`: `identity`, `system_mechanics.system_id = "dnd5e"`, and sheet from `Dnd5ePlugin().default_pc_sheet()` (see backend tests).

Minimal shape:

```json
{
  "identity": {
    "name": "Aldric",
    "concept": "Fighter",
    "current_location_id": "00000000-0000-0000-0000-000000000001"
  },
  "system_mechanics": {
    "system_id": "dnd5e",
    "schema_version": "1",
    "sheet": { "... default_pc_sheet fields ..." }
  }
}
```

### 4.5 Roll (player)

```powershell
$roll = @{
  roll_type = "skill_check"
  dice_expression = "1d20"
  modifier = 0
  context = @{ skill = "perception" }
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/campaigns/$campaignId/my-sheet/roll" -Body $roll -ContentType "application/json" -Headers $playerHeaders
```

**Pass criteria:** 201/200 responses; roll payload includes resolved D&D mechanics (total, natural roll, etc.).

OpenAPI: http://127.0.0.1:8000/docs after backend is healthy.

---

## 5. Bugs found / fixes applied

| Issue | Severity | Fix |
|-------|----------|-----|
| Docker backend missing `pgvector` vs current `requirements.txt` | **High** (was blocking API) | **Fixed** via `docker compose build backend --no-cache` (2026-06-17). |
| Circular import `scenes` ↔ `master` on app startup | **High** (was blocking API) | **Fixed** (2026-06-17): moved `load_scene_state` import inside `build_master_assist_response` in `master.py` (breaks `scenes` → `master` → `scenes` cycle at module load). |
| Local venv/global Python missing `pgvector` until explicit install | **Medium** (blocks full app import on host) | Run `pip install -r requirements.txt` from `backend/` (not committed). |
| D&D rules/combat logic | ï¿½ | No defects found in targeted tests. |

**No git commit --trailer "Co-authored-by: Cursor <cursoragent@cursor.com>"** per request.

---

## 6. Recommended next steps

1. Run section 4 smoke checklist (or UI: Create Campaign → D&D 5e → character sheet → roll).
2. Optionally add CI step: `docker compose build backend && docker compose run --rm backend python -c "import pgvector"`.

### Circular import fix (2026-06-17)

- **Change:** `backend/app/services/master.py` — removed top-level `from app.services.scenes import load_scene_state`; import deferred inside `build_master_assist_response`.
- **Verify:** `python -c "from app.main import app"` (host OK); `docker compose up -d backend` + health curl OK.
- **`fix_campaign_game_system.py`:** script exists at `backend/scripts/`; host DB unreachable (asyncpg on Windows); ran via Docker with scripts volume mount — 1 PC (`Norman`) updated `system_mechanics.system_id` `generic` → `dnd5e`; campaigns already valid.

