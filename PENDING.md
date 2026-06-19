> Actualizado jun 2026 — refleja el código en `main` (post avatares + polish v1-prep). No es sprint plan.

# PENDING — RolePBP

---

## ✅ Completado

### Plataforma core

- Auth JWT: registro, login, `GET /auth/me`, rehidratación en `AuthBootstrap`
- Campañas: crear, listar, detalle, `PATCH` (nombre, tono, `game_system`), miembros (invitar, listar, expulsar)
- Escenas: crear, activar, pausar, **cerrar** (`POST /scenes/{id}/close`), numeración, `display_name`
- `SceneState` anidado alineado con schema (`metadata`, `context`, `turn_management`, `memory_settings`, `state_flags`, `combat`)
- Entidades JSONB: CRUD NPC/PC/LOCATION/FACTION/RELATIONSHIP + editor en `WorldPage` (NPC ficha; ubicación/facción/relación `WorldEntityEditor`)
- **Avatares de entidad**: subida/eliminación vía API, retrato en ficha, chat, combate y dados
- Chat REST + WebSocket; mensajes, dados, lectura, borrado de mensaje
- **Chat OOC** por campaña: mensajes públicos y susurros, REST + WebSocket, pestaña «Fuera de personaje»
- Biblioteca de documentos: subida, extracción TXT/MD/PDF/DOCX, indexación RAG al subir
- Docker Compose: PostgreSQL pgvector, volúmenes `campaign_uploads` y `data/manuals`

### IA / RAG

- **pgvector** `campaign_memory` (migración 004) — ChromaDB retirado
- **semantic_cache** (migración 009) con lookup/store en búsquedas
- Embeddings OpenAI (`text-embedding-3-small`) cuando hay clave
- Shadow Master: LLM + RAG + manuales de sistema + `focus_entity_id` en backend
- **Modos Shadow Master**: `narrative`, `rules`, `campaign` con detección de intención y respuestas acotadas
- **`@asistente` jugador**: endpoint `POST /scenes/{id}/lore-assist`, pool `remaining_player_lore_tokens`, UI en `ChatComposer`
- Resumen de cierre de escena (LLM o fallback) indexado como `SCENE_SUMMARY`; visible en hub (`CampaignSceneLog`)
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
- `MasterDeskPage`: escena, jugadores, asistente (modos SM), ajustes de campaña
- Hub: resumen destacado de última escena cerrada en `CampaignSceneLog`
- Nav campaña: pestaña «Fuera de personaje» (hint OOC)
- WebSocket escena/OOC: reconexión con backoff exponencial (5 reintentos)
- Páginas huérfanas retiradas (`MasterPanelPage`, `MasterScreenPage`, `EntitiesPage`, `CreateCampaignForm`)
- Docker Compose prod: `docker-compose.prod.yml`, `frontend/Dockerfile.prod`, nginx estático
- `.env.production.example` + `docs/DEPLOY.md`
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
6. **WebSocket avanzado** — reauth en cierre `4401`; rate limit acciones WS

### Calidad y deuda

- Validación entidades: refs cruzadas (`faction_id`, `location_id`); 1 `ARC_MANIFEST` por campaña; auto-crear al crear campaña
- **ARC_MANIFEST**: schema + CRUD backend; sin formulario UI ni auto-creación en campaña nueva
- **Conocimiento PJ / RAG NPC**: no priorizado — el chat de escena es la fuente principal; las entidades van al snapshot de Shadow Master, no a chunks RAG dedicados por NPC
- Rate limiting ampliado: `@asistente`, cierre escena, Redis en prod (hoy solo `/master/assist` en memoria)
- Auth: recuperación de contraseña; refresh token
- TanStack Query: hooks dedicados donde aún hay llamadas inline (`useMasterAssistMutation`, etc.)
- Zod/RHF en formularios de entidad/campaña/escena
- PWA: iconos PNG 192/512, `apple-touch-icon`, verificar SW en prod
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
| Shadow Master LLM | ✅ modos narrative/rules/campaign |
| Avatares entidad | ✅ upload + chat/ficha |
| Chat OOC | ✅ REST + WS + susurros |
| Fichas + combate | ✅ 3 sistemas |
| Manuales sistema | ✅ infra; ⏳ PDFs + indexación manual |
| Mundo (facción/relación) | ✅ crear + editar UI; Shadow Master snapshot |
| ARC_MANIFEST | ⏳ schema/CRUD; sin UI |
| WS reconexión básica | ✅ escena + OOC |
| Tests + CI | ✅ backend; frontend build only |
| ChromaDB | ❌ retirado |

---

## 🚀 Prep producción $0 (repo only — sin deploy)

Checklist mínimo antes de desplegar:

- [x] `docker-compose.prod.yml` + `frontend/Dockerfile.prod`: backend sin `--reload`, nginx sirviendo `frontend/dist`
- [x] `.env.production.example` y `docs/DEPLOY.md`
- [ ] Variables en plataforma: `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_KEY`, `UPLOAD_DIR` persistente
- [x] Migraciones Alembic en entrypoint del contenedor backend
- [x] CORS / `VITE_API_URL` documentados (proxy nginx same-origin en compose prod)
- [x] Healthcheck `/health` para el orquestador

Sugerencia de stack gratuito: **Vercel** (frontend estático + PWA) + **Railway** o **Render** free tier (FastAPI + Postgres; Render Postgres expira a los 90 días — Railway suele ser más estable para hobby). Alternativa todo-en-uno: **Fly.io** (app + volume para uploads) o **Render** web service + Postgres externo (Neon free tier).
