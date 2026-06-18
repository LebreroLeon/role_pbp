> Actualizado jun 2026 — refleja el código en `main` (commit ~526e8e1). No es sprint plan.

# PENDING — RolePBP

---

## ✅ Completado

### Plataforma core

- Auth JWT: registro, login, `GET /auth/me`, rehidratación en `AuthBootstrap`
- Campañas: crear, listar, detalle, `PATCH` (nombre, tono, `game_system`), miembros (invitar, listar, expulsar)
- Escenas: crear, activar, pausar, **cerrar** (`POST /scenes/{id}/close`), numeración, `display_name`
- `SceneState` anidado alineado con schema (`metadata`, `context`, `turn_management`, `memory_settings`, `state_flags`, `combat`)
- Entidades JSONB: CRUD NPC/PC/LOCATION + editor en `WorldPage`
- Chat REST + WebSocket; mensajes, dados, lectura, borrado de mensaje
- Biblioteca de documentos: subida, extracción TXT/MD/PDF/DOCX, indexación RAG al subir
- Docker Compose: PostgreSQL pgvector, volúmenes `campaign_uploads` y `data/manuals`

### IA / RAG

- **pgvector** `campaign_memory` (migración 004) — ChromaDB retirado
- **semantic_cache** (migración 009) con lookup/store en búsquedas
- Embeddings OpenAI (`text-embedding-3-small`) cuando hay clave
- Shadow Master: LLM + RAG + manuales de sistema + `focus_entity_id` en backend
- **`@asistente` jugador**: endpoint `POST /scenes/{id}/lore-assist`, pool `remaining_player_lore_tokens`, UI en `ChatComposer`
- Resumen de cierre de escena (LLM o fallback) indexado como `SCENE_SUMMARY`
- Purga de `semantic_cache` al cerrar escena
- Borrado de chunks RAG al eliminar documento de biblioteca

### Fichas, combate y PBP

- Plugins de reglas: `dnd5e`, `cyberpunk_red`, `vtm_v5`, fallback genérico (`backend/app/rules/`)
- Fichas UI: `/ficha` (jugador), `/fichas` (mesa), formularios por sistema
- Combate: iniciativa, ataque, daño en entidades, paneles en chat (`InitiativeOrderPanel`, `SceneAttackSheet`)
- PBP: `pbp_enabled`, orden manual/iniciativa/atributo, enforcement backend, avance de turno
- Presencia NPC/jugador en escena (`presence` API)

### Manuales de sistema (infra)

- Tablas `system_manual_sources` / `system_manual_memory` (migración 008)
- `SYSTEM_MANUALS_DIR` en config y Docker
- API `GET /system-manuals/{system_id}/status`
- UI `SystemManualsPanel` en `LibraryPage`
- Script `backend/scripts/index_system_manuals.py` (indexación PDF → pgvector)
- RAG fusiona chunks de campaña + manuales en Shadow Master y `@asistente`

### UI / DX

- Componentes `Modal`, `ConfirmDialog`, `Switch`
- `MasterDeskPage`: escena, jugadores, asistente, ajustes de campaña
- CI GitHub Actions: `pytest` backend + `npm run build` frontend
- Tests backend: auth, combate, PBP, escenas, RAG, fichas, manuales, documentos (~12 suites)

---

## 🔴 Bloqueantes — acción manual del usuario

| Acción | Por qué |
|---|---|
| **`OPENAI_API_KEY` en `.env`** | Sin clave: embeddings, Shadow Master, `@asistente`, resumen de cierre y indexación devuelven vacío o fallback. Copiar de `.env.example`. |
| **PDFs en `data/manuals/{system_id}/`** | Los manuales oficiales no van en git. Copiar copias licenciadas (ej. D&D desde Descargas) según `data/manuals/dnd5e/README.md`. |
| **Ejecutar indexador de manuales** | Tras copiar PDFs: `cd backend && python scripts/index_system_manuals.py --system dnd5e` (requiere clave OpenAI). |
| **`JWT_SECRET` fuerte en producción** | El default `change-me-in-production` no es seguro fuera de dev. |

---

## 🟡 Próximo sprint (priorizado por impacto)

### Alto impacto (sin nuevas deps)

1. **Indexar manuales** — tras PDFs + clave; verificar badge «Reglas disponibles» en biblioteca
2. **Archivado chat_buffer → RAG** — al superar `max_chat_buffer_size`, persistir mensajes antiguos antes de recortar (hoy solo trim en memoria)
3. **Comandos de chat** — parser `@npc ataca @pc`, `/attack` (backend + autocompletado `@` en compositor)
4. **Gestión campaña** — `DELETE /campaigns/{id}`; `PATCH` rol miembro (`MASTER` ↔ `PLAYER`); invitación por link/email
5. **Selector `focus_entity_id`** en pestaña Asistente de `MasterDeskPage` (backend ya lo usa)
6. **WebSocket** — reconexión con backoff; reauth en cierre `4401`; rate limit acciones WS

### Calidad y deuda

- Eliminar páginas huérfanas: `MasterPanelPage`, `MasterScreenPage`, `EntitiesPage`, `CreateCampaignForm`
- Validación entidades: refs cruzadas (`faction_id`, `location_id`); 1 `ARC_MANIFEST` por campaña; auto-crear al crear campaña
- Formularios `FACTION`, `RELATIONSHIP`, `ARC_MANIFEST` en `CreateEntityForm`
- Rate limiting ampliado: `@asistente`, cierre escena, Redis en prod (hoy solo `/master/assist` en memoria)
- Auth: recuperación de contraseña; refresh token
- TanStack Query: hooks dedicados donde aún hay llamadas inline (`useMasterAssistMutation`, etc.)
- Zod/RHF en formularios de entidad/campaña/escena
- PWA: iconos PNG 192/512, `apple-touch-icon`, verificar SW en prod
- Docker prod: backend sin `--reload`, frontend build estático + nginx
- Docs: sincronizar `docs/04_data_persistence.md`, `README.md` (quitar refs ChromaDB); retirar `CHROMA_PERSIST_DIR` de `.env.example`
- Tests: vitest frontend; E2E Playwright; más cobertura integración API

### Menor (fichas/combate)

- WS paridad REST para tiradas/combate
- `DiceRoller` con modificadores desde ficha
- Bloquear cambio de `game_system` si existen fichas mecánicas

---

## 🔵 Futuro (no priorizar ahora)

- **Audio** STT/TTS — diseño en `docs/06_audio_features.md`
- **Capacitor / APK** — Fase 2 arquitectura
- **Push notifications** — turno y alertas móvil
- Anthropic como proveedor LLM alternativo (`ANTHROPIC_API_KEY` ya en config, sin wiring)
- Escritorio PWA / Capacitor Desktop — Fase 3

---

## Referencia rápida docs ↔ código

| Capacidad | Estado |
|---|---|
| pgvector RAG | ✅ `campaign_memory` |
| semantic_cache | ✅ + purga al cerrar escena |
| SceneState anidado | ✅ |
| Cierre escena + WorldLog | ✅ (resumen LLM/fallback → RAG) |
| `@asistente` | ✅ endpoint + UI |
| Shadow Master LLM | ✅ (requiere clave) |
| Fichas + combate | ✅ 3 sistemas |
| Manuales sistema | ✅ infra; ⏳ PDFs + indexación manual |
| Tests + CI | ✅ backend; frontend build only |
| ChromaDB | ❌ retirado |
