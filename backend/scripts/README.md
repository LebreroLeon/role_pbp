# Scripts

## `fix_campaign_game_system.py`

Backfill `campaigns.game_system` to dnd5e and align PC `system_mechanics.system_id`.

```bash
docker cp backend/scripts/fix_campaign_game_system.py rolepbp-backend:/app/scripts/
docker exec rolepbp-backend python /app/scripts/fix_campaign_game_system.py [--dry-run]
```

## `index_system_manuals.py` (stub)

Escanea PDFs en `data/manuals/{system_id}/` para indexación RAG de reglas oficiales. Ver `docs/07_system_manuals.md`.

```bash
cd backend
python scripts/index_system_manuals.py --system dnd5e --dry-run
python scripts/index_system_manuals.py --all
```
