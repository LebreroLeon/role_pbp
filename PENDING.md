> Generado automáticamente — lista de trabajo pendiente de RolePBP. No es sprint plan.

# TODO exhaustivo — RolePBP

Estado base: MVP funcional con auth JWT, campañas, miembros, chat+WS, entidades JSONB, biblioteca de archivos, Shadow Master **prototipo** (ChromaDB + sugerencias hardcodeadas). Mucha documentación describe capacidades aún no implementadas o **desactualizada** respecto al código.

---

## Backend

### Persistencia y migraciones

- [ ] Crear migración Alembic `campaign_memory` con extensión `vector`, enum `memory_document_type`, columna `embedding vector(1536)` e índice HNSW — según `docs/04_data_persistence.md`
- [ ] Crear migración Alembic `semantic_cache` — según `docs/04_data_persistence.md` y `docs/03_ai_engine/rag_pipeline.md`
- [ ] Añadir **FK** faltantes en migraciones existentes: `scenes.campaign_id → campaigns.id`, `campaign_entities.campaign_id → campaigns.id`, `campaign_documents.campaign_id → campaigns.id` (`backend/alembic/versions/001_initial_schema.py`, `003_...`)
- [ ] Cambiar `campaign_entities.entity_type` de `String(32)` a `ENUM` PostgreSQL (`NPC|PC|FACTION|LOCATION|RELATIONSHIP|ARC_MANIFEST`) — `docs/04_data_persistence.md`
- [ ] Añadir índice GIN en `campaign_entities.document` — documentado en `docs/04_data_persistence.md`
- [ ] Implementar **archivado del chat_buffer**: al superar `max_chat_buffer_size`, indexar mensajes antiguos en memoria vectorial y eliminarlos del buffer (hoy solo se recorta en `backend/app/services/scenes.py`, sin archivado persistente)
- [ ] Persistir datos ChromaDB en Docker: montar volumen para `CHROMA_PERSIST_DIR` en `docker-compose.yml` (hoy no hay volumen; se pierde al reiniciar contenedor)

### SceneState — alinear con contrato canónico

- [ ] Refactorizar `backend/app/schemas/scene.py` para coincidir con `docs/02_data_models/scene_state_schema.json`: estructura anidada `metadata`, `context`, `turn_management`, `memory_settings`, `state_flags` (hoy es plano/incompatible)
- [ ] Añadir campos documentados ausentes: `max_player_lore_queries_per_scene`, `remaining_player_lore_tokens`, `conflict_mode_active`, `ai_alert_triggered`, `location_id`, `active_npc_ids`
- [ ] Soportar estado `CLOSED` en `scene_state.metadata.status` y en `scenes.status` (hoy solo `ACTIVE|PAUSED` en `SceneStatusType`)
- [ ] Actualizar `backend/app/services/scenes.py` y rutas WS/REST para leer/escribir la nueva estructura
- [ ] Migración de datos: transformar `scene_state` JSONB existente al nuevo formato
- [ ] Validar en backend que `post_message` / `roll_scene_dice` rechacen escenas `PAUSED` o `CLOSED` (hoy solo lo bloquea el frontend en `ChatPage.tsx`)
- [ ] Implementar **motor de turnos**: validar `current_turn_player_id` antes de aceptar mensajes de jugadores; avanzar turno tras acción válida
- [ ] Endpoint `POST /api/v1/scenes/{scene_id}/close` — documentado en `docs/03_ai_engine/rag_pipeline.md` (no existe)
- [ ] Endpoint/payload para editar `scene_objective`, `location_id`, `active_npc_ids`, `turn_order` al crear o actualizar escena
- [ ] Endpoint `GET /api/v1/campaigns/{campaign_id}/scenes` ya existe en `campaigns_mgmt.py` — falta lógica de negocio para escenas cerradas y creación de nueva escena tras cierre

### Entidades (`campaign_entities`)

- [ ] Validar referencias cruzadas al crear/actualizar: `faction_id`, `current_location_id`, `source_id`/`target_id` deben existir en la misma campaña (`backend/app/services/entities.py`)
- [ ] Enforzar **1 solo `ARC_MANIFEST` por campaña** — `docs/02_data_models/README.md`
- [ ] Crear `ARC_MANIFEST` vacío automáticamente al crear campaña (`backend/app/services/campaigns.py`)
- [ ] Endpoints de consulta por flags para RAG (NPCs `is_present_in_scene`, `is_dead`, etc.) — queries documentadas en `docs/04_data_persistence.md` §4
- [ ] `PUT /api/v1/entities/{entity_id}` existe en `entities.py` — sin uso en frontend

### Campañas y miembros

- [ ] `PATCH /api/v1/campaigns/{id}` — editar `name`, `tone`, `game_system`
- [ ] `DELETE /api/v1/campaigns/{id}` — borrado de campaña
- [ ] `DELETE /api/v1/campaigns/{id}/members/{user_id}` — expulsar jugador
- [ ] `PATCH` rol de miembro (`MASTER` ↔ `PLAYER`)
- [ ] Invitación requiere usuario pre-registrado (`campaigns.py`) — flujo de invitación por email/link pendiente

### Auth

- [ ] Recuperación/cambio de contraseña
- [ ] Refresh token o estrategia de renovación JWT (hoy solo access token 7 días en `config.py`)
- [ ] Validación de `JWT_SECRET` débil en producción (`change-me-in-production`)
- [ ] Endpoint server-side de logout / revocación (opcional; hoy solo cliente en `useAuthMutations.ts`)
- [ ] Usar `GET /api/v1/auth/me` en frontend para rehidratar sesión al arrancar (`api/client.ts` definido, no consumido)

### Biblioteca de documentos

- [ ] Pipeline de extracción de texto (PDF, DOCX, TXT, MD) desde `backend/app/services/documents.py`
- [ ] Indexar contenido de documentos subidos en memoria RAG al subir/actualizar
- [ ] Borrar chunks RAG asociados al eliminar documento (`delete_campaign_document`)

### Dados y reglas

- [ ] Integrar modificadores de tirada desde ficha PC (`system_mechanics.stats_summary`) — `backend/app/services/dice.py` acepta `modifier`/`skill_checked` pero no los calcula
- [ ] Perfiles de dados/reglas por `game_system` de campaña — `frontend/src/features/campaign/gameSystems.ts` dice que hoy es solo metadata

### WebSockets

- [ ] Reconexión y manejo de token expirado en `backend/app/api/routes/ws.py` (cierre `4401`)
- [ ] Rate limiting en acciones WS (`message`, `dice`)
- [ ] Validación de turno y estado de escena en acciones WS

### Shadow Master (endpoint actual)

- [ ] Rate limiting en `POST /api/v1/master/assist` — `docs/03_ai_engine/rag_pipeline.md` (10 req/min)
- [ ] Usar `focus_entity_id` de `MasterAssistRequest` (`backend/app/schemas/master.py`) en `build_master_assist_response` — hoy ignorado

### Configuración (`.env` / `config.py`)

- [ ] Conectar `OPENAI_API_KEY` y `ANTHROPIC_API_KEY` — definidos en `.env.example` y `config.py`, sin uso
- [ ] Añadir a `.env.example` y `config.py`: `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `LLM_PROVIDER`, `LLM_MODEL`, `REDIS_URL`, `MAX_UPLOAD_BYTES`
- [ ] Eliminar `CHROMA_PERSIST_DIR` tras migración a pgvector
- [ ] `httpx` en `requirements.txt` sin uso — conectar al integrar LLM

---

## Frontend

### Páginas huérfanas / código muerto

- [ ] Eliminar o reintegrar `frontend/src/pages/MasterPanelPage.tsx` — duplica asistente de `MasterDeskPage.tsx`, sin ruta en `App.tsx`
- [ ] Eliminar o reintegrar `frontend/src/pages/MasterScreenPage.tsx` — duplica mesa del máster, sin ruta en `App.tsx`
- [ ] Eliminar o reintegrar `frontend/src/pages/EntitiesPage.tsx` — sustituida por `WorldPage.tsx`, sin ruta en `App.tsx`
- [ ] Eliminar `frontend/src/features/campaign/CreateCampaignForm.tsx` — exportada pero no usada; reemplazada por `CreateCampaignWizard.tsx`
- [ ] Eliminar `frontend/src/config/constants.ts` (`DEV_PLACEHOLDERS`) si ya no aplica tras auth real

### Endpoints sin UI

- [ ] Editor de entidad (`PUT /entities/{id}`) — vista detalle + formulario edición en `WorldPage` / nueva ruta
- [ ] `GET /entities/{id}` — ficha individual
- [ ] Historial de escenas (`GET /campaigns/{id}/scenes`) — listado en Mesa del Máster
- [ ] **Cierre de escena** — botón en `MasterDeskPage.tsx` cuando exista endpoint `/scenes/{id}/close`
- [ ] Selector `focus_entity_id` en pestaña Asistente de `MasterDeskPage.tsx`
- [ ] Edición de campaña (`name`, `tone`, `game_system`) en pestaña Campaña de `MasterDeskPage.tsx`
- [ ] Gestión avanzada de miembros: quitar jugador, cambiar rol

### UI sin backend completo

- [ ] Chat **consultor de lore para jugadores** (`@asistente`) — prometido en `README.md` y `docs/03_ai_engine/rag_pipeline.md`; sin endpoint ni UI
- [ ] Indicador y enforcement de **turno actual** en `ChatPage.tsx` / `ChatComposer.tsx`
- [ ] Editor de objetivo de escena, ubicación activa y NPCs en escena
- [ ] Formularios de creación para `FACTION`, `RELATIONSHIP`, `ARC_MANIFEST` — solo NPC/LOCATION/PC en `CreateEntityForm.tsx`
- [ ] Selector real de `faction_id` / `current_location_id` al crear NPC/PC — hoy `PLACEHOLDER_UUID` en `entityDefaults.ts`
- [ ] Extracción automática de NPCs desde PDF — mencionada en `ImportExportPanel.tsx`
- [ ] IA consultando biblioteca — textos "más adelante" en `LibraryPage.tsx`, `DocumentLibrary.tsx`
- [ ] Notificaciones de turno — `README.md` ("notificaciones inteligentes de turno")
- [ ] `skill_checked` y modificadores en `DiceRoller.tsx` — backend los soporta parcialmente

### TanStack Query / convenciones (`.cursorrules`)

- [ ] Crear `useMasterAssistMutation` — hoy `MasterDeskPage.tsx` llama `api.masterAssist` con `useState`
- [ ] Crear `useUpdateSceneStatusMutation` — hoy lógica inline en `MasterDeskPage.tsx`
- [ ] Crear `useCreateSceneMutation`, `usePostMessageMutation`, `useRollDiceMutation` — hoy inline en `ChatPage.tsx`
- [ ] Crear `useUpdateEntityMutation`, `useEntityDetailQuery`
- [ ] Crear `useCampaignScenesQuery` para listado de escenas
- [ ] Añadir query keys faltantes en `api/queryKeys.ts` (scenes list, master assist, etc.)

### Tipos y validación

- [ ] Alinear `frontend/src/api/types.ts` (`SceneState`) con schema canónico y backend — hoy solo `campaign_id`, `status`, `scene_objective`, `chat_buffer`
- [ ] Schemas Zod para formularios de entidades, campaña y escena — hoy solo `frontend/src/schemas/auth.ts` (`.cursorrules` exige RHF+Zod en todos los formularios)
- [ ] Migrar formularios de entidades/campaña de estado local a React Hook Form + Zod

### PWA (Fase 1 arquitectura)

- [ ] Verificar build producción con `vite-plugin-pwa` (`frontend/vite.config.ts`) — `devOptions.enabled: false`; falta validar `npm run build`
- [ ] Iconos PWA: solo `frontend/public/icon.svg` — generar PNG 192×192 y 512×512 para instalación Android
- [ ] Añadir `apple-touch-icon`, `description`, `manifest` link en `frontend/index.html`
- [ ] Estrategia offline/cache para assets estáticos y manejo de API sin conexión
- [ ] Registrar/verificar service worker en producción (`main.tsx` no importa registro PWA explícito)

### Mobile-first (docs `01_architecture_overview.md`)

- [ ] Navegación móvil tipo drawer/tabs para campaña (hoy nav horizontal en `CampaignLayout.tsx`)
- [ ] Auditoría de áreas táctiles ≥ 44×44 px
- [ ] Breakpoints 360–430 px — revisar CSS en `App.css`, `index.css`, `theme.css`

### WebSocket cliente

- [x] Mostrar errores WS (`event: error`) en `ChatPage` vía `useSceneWebSocket.onError`
- [ ] Reconexión con backoff en `frontend/src/hooks/useSceneWebSocket.ts`
- [ ] Reautenticación si WS cierra con `4401`
- [ ] Indicador de "tu turno" / bloqueo UI cuando no es el turno del jugador

### Capacitor / APK (Fase 2 arquitectura)

- [ ] Instalar y configurar `@capacitor/core`, `@capacitor/cli`, `capacitor.config.ts`
- [ ] Proyecto Android (`npx cap add android`) y build APK desde `vite build`
- [ ] Configurar URL base API para app nativa (`VITE_API_URL` en build móvil)
- [ ] Splash screen, status bar, permisos de red
- [ ] Pipeline iOS (Fase 2) — no iniciado
- [ ] Evaluación escritorio PWA/Capacitor Desktop (Fase 3) — no iniciado

---

## IA / RAG

### Migración ChromaDB → pgvector

- [ ] Reescribir `backend/app/services/rag.py` para SQLAlchemy + pgvector (`campaign_memory`) — `.cursorrules` §3.4 y `docs/04_data_persistence.md` §6
- [ ] Eliminar dependencia `chromadb` de `requirements.txt`
- [ ] Añadir cliente embeddings (OpenAI `text-embedding-3-small` u otro) y dimensión configurable
- [ ] Búsqueda por `<=>` coseno con `rag_top_k_matches` desde `scene_state.memory_settings`

### Pipeline RAG completo (`docs/03_ai_engine/rag_pipeline.md`)

- [ ] **Paso 0**: semantic cache lookup antes de embeddings
- [ ] **Paso 1**: generación de embeddings de la consulta
- [ ] **Paso 2**: búsqueda vectorial en `campaign_memory`
- [ ] **Paso 3**: extracción estado PostgreSQL JSONB (NPCs, PCs, facciones, ubicaciones, arco) con filtrado de secretos por rol
- [ ] **Paso 4**: construcción del Sándwich `[Flags] + [RAG] + [Buffer] + [Input]`
- [ ] **Paso 5**: persistir respuesta en `semantic_cache`
- [ ] Implementar `state_snapshot_hash` (NPCs activos, `is_dead`, misiones, `world_threat_level`, etc.)
- [ ] Reglas de invalidación de caché: cierre escena, mutación flags, edición secretos, TTL

### Integración LLM (Shadow Master)

- [ ] Conectar OpenAI o Anthropic en `backend/app/services/master.py` — hoy sugerencias hardcodeadas
- [ ] Eliminar stub en `backend/app/schemas/master.py` (`note: "Stub response — connect LLM provider..."`)
- [ ] Definir e implementar system prompts para los 3 roles documentados en `README.md`: Consultor de Reglas, Shadow Master, Secretario
- [ ] Selección de proveedor/modelo vía config (`LLM_PROVIDER`, `LLM_MODEL`)

### Cierre de escena automatizado

- [ ] Consolidar WorldLog con LLM al cerrar escena
- [ ] Indexar resumen en `campaign_memory` (`SCENE_SUMMARY` / `WORLDLOG`)
- [ ] Mutar documentos JSONB en `campaign_entities` según consecuencias de la escena
- [ ] Resetear `remaining_player_lore_tokens` al valor de `max_player_lore_queries_per_scene`
- [ ] Purgar `semantic_cache` de la campaña
- [ ] UI de confirmación y progreso en `MasterDeskPage.tsx`

### Consultor de lore jugador (`@asistente`)

- [ ] Endpoint dedicado (ej. `POST /api/v1/scenes/{id}/assist` o comando en chat) con pool `remaining_player_lore_tokens`
- [ ] Filtrado estricto: sin `secret_*`, solo conocimiento del PJ
- [ ] Rate limit / 429 con mensaje explicativo — `docs/03_ai_engine/rag_pipeline.md`
- [ ] UI de chat secundario o comando `@asistente` en `ChatPage.tsx`
- [ ] Resolver tensión docs: `.cursorrules` dice "jugadores nunca llaman al LLM" vs `rag_pipeline.md` y `README.md` que sí documentan consultas jugador con pool limitado

### Rate limiting

- [ ] Middleware/store rate limit (memoria dev; Redis o `rate_limit_buckets` prod) — `docs/03_ai_engine/rag_pipeline.md`
- [ ] Límites: `/master/assist` 10/min, cierre escena 2/hora, logging de abusos

### Indexación de contenido

- [ ] Indexar mensajes de chat con `document_type=CHAT_LOG` y metadata (`scene_id`, `sender_id`) — hoy Chroma sin embeddings OpenAI
- [ ] Indexar lore de NPCs (`NPC_LORE`) al crear/actualizar entidades
- [ ] Indexar documentos de biblioteca tras extracción de texto
- [ ] Job en background para re-indexación masiva (sin llamar al LLM)

---

## Infra / Docs

### Documentación desactualizada

- [ ] Actualizar `docs/04_data_persistence.md` §7: `campaign_entities`, `campaign_members` y auth **sí están implementados**; pendientes reales: `campaign_memory`, `semantic_cache`, migración ChromaDB
- [ ] Actualizar `docs/01_architecture_overview.md` §2: auth JWT ya implementada ("se implementarán en el MVP")
- [ ] Actualizar `README.md` §5: sigue citando ChromaDB/Pinecone; arquitectura objetivo es pgvector
- [ ] Actualizar `.cursorrules` §3.5: `LoginForm`/`RegisterForm`/`CampaignList` ya no son "futuro"
- [ ] Documentar tabla `campaign_documents` (no está en `docs/04_data_persistence.md`)
- [ ] Documentar discrepancia `scene_state` código vs `scene_state_schema.json` hasta que se alinee

### `.env.example` vs código

- [ ] Documentar variables LLM/embeddings/Redis pendientes
- [ ] Documentar `UPLOAD_DIR`, `max_upload_bytes` (solo en `config.py`)
- [ ] Documentar `jwt_algorithm`, `jwt_expire_minutes`
- [ ] Plan de retirada de `CHROMA_PERSIST_DIR`

### Docker / despliegue

- [ ] `docker-compose.yml`: healthcheck backend/frontend; servicio Redis si aplica
- [ ] Backend producción: quitar `--reload` del `CMD` en `backend/Dockerfile`
- [ ] Frontend producción: imagen con `npm run build` + nginx/serve estático, no solo `vite dev` (`frontend/Dockerfile`)
- [ ] Volumen persistente para uploads (`campaign_uploads`) — ya existe; verificar backup
- [ ] Compose/stack de producción (HTTPS, dominio, CORS prod)
- [ ] Scripts `scripts/dev-*.ps1`: añadir comandos test, lint, migrate-only, build

### Capacitor / distribución

- [ ] Documentar pasos Capacitor Android en README o nuevo doc de despliegue
- [ ] Checklist Play Store / firma APK

---

## Calidad

### Tests (cero en el repo)

- [ ] Configurar `pytest` + `pytest-asyncio` en `backend/` con fixtures de BD test
- [ ] Tests unitarios: `dice.py`, `entities.py` (validación/strip secrets), `scenes.py` (turnos, buffer, PAUSED)
- [ ] Tests integración API: auth, campaigns, entities, scenes, master/assist, documents
- [ ] Test de seguridad: jugador **nunca** recibe `secret_lore_master` en `entities.py`
- [ ] Configurar `vitest` + Testing Library en `frontend/`
- [ ] Tests componentes: `ChatEntry`, `CreateEntityForm`, `RoleGate`, `ProtectedRoute`
- [ ] Tests hooks: `useSceneWebSocket`, mutations
- [ ] Tests contrato: Pydantic models vs JSON Schema en `docs/02_data_models/` (script o suite dedicada)
- [ ] Tests migraciones Alembic (upgrade/downgrade)
- [ ] E2E con Playwright: flujo registro → crear campaña → iniciar escena → enviar mensaje

### CI / tooling

- [ ] Crear `.github/workflows/ci.yml`: lint + test backend + test frontend + build
- [ ] Añadir `ruff` / `mypy` (backend) y `eslint` / `typescript` strict check (frontend) — ninguno configurado
- [ ] Pre-commit hooks (format, lint, tests rápidos)
- [ ] `package.json`: scripts `lint`, `test`, `typecheck`
- [ ] `requirements-dev.txt` o extras para herramientas de desarrollo

### Seeds y datos de desarrollo

- [ ] Script seed desde `examples` de `docs/02_data_models/*.json` — recomendado en `docs/02_data_models/README.md`
- [ ] Datos demo: campaña con NPCs, arco, escena activa para pruebas manuales

### Deuda técnica explícita en código/docs

- [ ] `backend/app/schemas/master.py`: respuesta stub Shadow Master
- [ ] `backend/app/services/master.py`: sugerencias estáticas, sin LLM
- [ ] `backend/app/services/rag.py`: prototipo ChromaDB — migración pendiente (`.cursorrules` L261)
- [ ] `frontend/src/features/campaign/gameSystems.ts`: "futuro contexto IA"
- [ ] `frontend/src/features/library/DocumentLibrary.tsx`, `LibraryPage.tsx`: "La IA los usará más adelante"
- [ ] `frontend/src/features/entities/ImportExportPanel.tsx`: "extracción automática desde PDFs… con integración de IA"
- [ ] `MasterDeskPage.tsx` pestaña Asistente: "prototipo… IA completa en fase posterior"

---

## Fichas de personaje y combate

> Diseño: `docs/05_character_sheets_and_combat.md`. Implementar en fases; no empezar combate antes de alinear `SceneState` (§ SceneState arriba).

### Fase 0 — Preparación

- [ ] Documentar extensión `scene_state.combat` en `docs/02_data_models/scene_state_schema.json` (`initiative_order`, `round`, `current_turn_index`)
- [ ] Añadir tipo de mensaje `COMBAT` (y campos opcionales en `DICE_ROLL`: `entity_id`, `roll_type`, `roll_details`) al schema de chat en `scene_state_schema.json`
- [ ] Crear JSON Schema hijos de ficha: `entity_pc_dnd5e_sheet.json`, `entity_pc_cyberpunk_red_sheet.json`, `entity_pc_vtm_v5_sheet.json` (+ variantes NPC)
- [ ] Endpoint `GET /api/v1/campaigns/{campaign_id}/entities/mine` — PC del usuario autenticado (1 por campaña)
- [ ] Enforzar en backend: un jugador solo puede `PUT` su PC; Máster edita cualquier entidad
- [ ] UI `PUT /entities/{id}` — editor de entidad (prerrequisito del panel de ficha)

### Fase 1 — Motor de reglas y perfiles de sistema

- [ ] Crear `backend/app/game_systems/` con `GameSystemRegistry`, `GameSystemPlugin` (Protocol) y `GenericFallbackPlugin`
- [ ] Mover/ampliar `backend/app/services/dice.py` → soporte pools d10, percentil según `dice_mode`
- [ ] Implementar plugin `dnd5e` (validación sheet, `default_pc_sheet`, tiradas: ability/skill/save/attack/damage/initiative)
- [ ] Implementar plugin `cyberpunk_red` (stats, skill pool d10, regla del mayor dado)
- [ ] Implementar plugin `vtm_v5` (atributos + skills, pool éxitos 6+, daño superficial/agravado)
- [ ] Crear `frontend/src/features/campaign/gameSystemProfiles.ts` — `sheetTemplateId`, `diceMode`, `supportedRollTypes`, `combatEnabled`
- [ ] Enlazar wizard (`CreateCampaignWizard.tsx`): preview del perfil al elegir sistema
- [ ] Al crear PC, usar plantilla del `campaign.game_system` en lugar de `system_name: "agnóstico"` (`entityDefaults.ts`)

### Fase 2 — Panel del jugador (D&D 5e primero)

- [ ] Ruta `/campaigns/:id/ficha` + enlace en `PLAYER_LINKS` / `MASTER_LINKS` (`CampaignLayout.tsx`)
- [ ] `PlayerSheetPage` — formulario D&D 5e (RHF + Zod): abilities, skills, AC, HP, ataques básicos
- [ ] Wizard de creación de PC si el jugador no tiene ficha en la campaña
- [ ] Endpoint `POST /api/v1/scenes/{scene_id}/rolls` — `roll_type`, `entity_id`, contexto (skill, dc, weapon_id)
- [ ] Servicio `backend/app/services/rolls.py` → `RuleEngine.resolve_roll()` → append `DICE_ROLL` enriquecido
- [ ] Componente `RollResultCard` en chat — mostrar éxito/fracaso, dados, modificadores
- [x] Acciones rápidas de combate en `ChatPage.tsx` — `QuickCombatActions.tsx` + `POST /scenes/{id}/combat/attack`
- [ ] WS action `roll` con paridad REST (`ws.py`)

### Fase 3 — Combate e iniciativa

- [ ] Servicio `backend/app/services/combat_scene.py` — start/end combat, iniciativa, avance de turno
- [ ] `POST /scenes/{id}/combat/start` — tira iniciativa para NPCs en `active_npc_ids` + PCs presentes
- [ ] `POST /scenes/{id}/combat/end`, `PATCH /scenes/{id}/combat/turn`
- [ ] Sincronizar `state_flags.conflict_mode_active` con `combat.is_active`
- [ ] `CombatTracker` / `InitiativePanel` en `ChatPage.tsx` — orden, PV actuales, turno resaltado
- [ ] Parser `backend/app/services/chat_commands.py` — `@origen ataca @destino`, `/attack @origen to @destino`
- [ ] `CombatResolver` — ataque → tirada → daño → `apply_damage` en documento entidad
- [ ] Mensajes `COMBAT` en `chat_buffer` con payload estructurado `combat_event`
- [ ] Permisos: jugador puede atacar con su PC; Máster con cualquier entidad en escena
- [ ] Actualizar flags al 0 HP: `is_incapacitated` (PC), `is_dead` (NPC)
- [ ] Resolución de menciones `@` contra entidades en escena (nombre fuzzy, desambiguación UI)

### Fase 4 — Cyberpunk RED

- [ ] Formulario ficha RED en `frontend/src/features/character-sheet/systems/cyberpunk_red/`
- [ ] Tiradas skill pool y combate con daño directo + umbral herido grave en UI
- [ ] Armas RED en bloque `weapons[]` con integración a `/attack`

### Fase 5 — Vampiro V5

- [ ] Formulario ficha V5 (atributos, skills, health tracks, hunger, willpower)
- [ ] Tiradas pool V5 y aplicación de daño superficial/agravado
- [ ] Indicador de hambre en ficha y opcional en combate

### Fase 6 — Pulido y calidad

- [ ] Autocompletado `@` en `ChatComposer.tsx` (entidades en escena + alias)
- [ ] Ayuda contextual de comandos `/` en compositor de chat
- [ ] Bloquear cambio de `game_system` en campaña si existen fichas mecánicas (`PATCH campaigns`)
- [ ] Tests unitarios: plugins dnd5e/red/vtm, `CombatResolver`, `ChatCommandParser`
- [ ] Test E2E: campaña D&D → crear ficha → escena → `/attack @npc to @pc` → PV actualizados
- [ ] Actualizar `docs/02_data_models/README.md` — sección fichas por sistema y `system_agnostic: false`
- [ ] Actualizar `README.md` con enlace a `docs/05_character_sheets_and_combat.md`

---

## Audio en escena (STT / TTS)

> Diseño: `docs/06_audio_features.md`. Objetivo: narrar jugadas sin escribir (STT) y escuchar la escena sin leer (TTS). Independiente de fichas/combate; puede implementarse en paralelo al chat actual.

### STT — grabar audio y transcribir en chat

- [ ] **Frontend `ChatComposer.tsx`**: botón micrófono (toggle grabar/detener) junto al enviar; estados visuales `idle | recording | processing | error`; deshabilitar envío de texto mientras graba o transcribe
- [ ] **Frontend**: usar `MediaRecorder` (WebM/Opus) con límite de duración configurable (ej. 60–120 s); preview opcional de waveform o contador de tiempo
- [ ] **Frontend**: hook `useAudioRecorder` — permisos, cleanup al desmontar, cancelar grabación sin enviar
- [ ] **Backend** `POST /api/v1/scenes/{scene_id}/transcribe` — aceptar `multipart/form-data` (`audio` blob) o `base64`; validar tamaño (`MAX_UPLOAD_BYTES` / límite STT dedicado)
- [ ] **Backend servicio STT**: integrar OpenAI Whisper (`whisper-1` o API transcriptions) cuando `OPENAI_API_KEY` está configurada — idioma configurable (`es` por defecto)
- [ ] **Fallback STT cliente**: si no hay clave de servidor o usuario prefiere offline, transcribir con Web Speech API en el navegador y enviar solo texto vía `post_message` existente — documentar limitaciones (Chrome, sin Firefox, calidad variable)
- [ ] Tras transcripción exitosa en servidor: append mensaje `PLAYER`/`MASTER` en `chat_buffer` con el texto transcrito (mismo flujo que `post_message`); broadcast WS `message`
- [ ] Metadatos opcionales en mensaje: `source: "stt"`, `audio_duration_ms`, `stt_provider` — extender schema de entrada de chat si hace falta
- [ ] Rate limiting STT (ej. 20 req/min por usuario) — evitar abuso de API Whisper
- [ ] UI de error: micrófono denegado, archivo demasiado grande, transcripción vacía, timeout API

### TTS — reproducir cada mensaje de la escena

- [ ] **Frontend `ChatEntry.tsx`**: botón play/pause por mensaje de texto (no en `DICE_ROLL`/`COMBAT` salvo texto narrativo); icono accesible con `aria-label`
- [ ] **Frontend**: hook `useSceneTTS` — una sola reproducción activa; al iniciar otra, pausar la anterior; estado `loading | playing | paused | error`
- [ ] **Backend** `POST /api/v1/tts/synthesize` — body `{ text, voice?, language? }`; respuesta `audio/mpeg` o URL temporal; truncar texto largo (ej. 4 000 caracteres) con aviso en UI
- [ ] **Backend proveedor TTS (documentar y elegir uno primero)**:
  - OpenAI `tts-1-hd` — voces `onyx`/`fable` como narrador; buena calidad, coste por carácter
  - ElevenLabs — voces premium audiolibro; requiere `ELEVENLABS_API_KEY` y cuenta
  - Azure Cognitive Services Neural TTS — `es-ES-AlvaroNeural` / `es-ES-ElviraNeural`; enterprise, región EU
- [ ] Config `config.py` + `.env.example`: `TTS_PROVIDER`, `TTS_VOICE`, `TTS_MODEL`, claves por proveedor; selección vía env sin hardcode
- [ ] Caché opcional de audio TTS por hash `(text + voice + provider)` — filesystem o Redis; TTL 7 días; reducir coste en re-lecturas
- [ ] Rate limiting TTS (ej. 30 req/min por usuario o por campaña)
- [ ] No exponer claves TTS al cliente: siempre proxy vía backend (excepto fallback Web Speech API `speechSynthesis` documentado como degradación)

### Almacenamiento de audios (opcional vs solo texto)

- [ ] **Modo por defecto (MVP)**: solo persistir texto transcrito en `chat_buffer`; no guardar blob de grabación
- [ ] **Modo opcional**: subir audio original a biblioteca/uploads (`campaign_uploads/stt/{scene_id}/`) con referencia en mensaje (`audio_url`, `audio_mime`)
- [ ] Política de retención: borrar audios STT al cerrar escena o tras N días — documentar en `docs/06_audio_features.md`
- [ ] TTS: no persistir por defecto (stream); persistir solo si caché activada

### PWA / mobile

- [ ] Permisos micrófono: solicitar al primer uso del botón STT; mensaje claro si el usuario deniega; reintento tras cambio en ajustes del sistema
- [ ] `MediaRecorder` en Android WebView/Capacitor: validar en Chrome Android y futuro APK; fallback a input `type=file` `accept="audio/*"` para subir archivo grabado nativamente
- [ ] iOS Safari: límites de autoplay TTS — botón play explícito (ya requerido); probar background suspend
- [ ] PWA instalada: icono/indicador cuando micrófono activo (privacidad UX)
- [ ] Documentar en README requisitos: HTTPS para `getUserMedia` (prod)

### Accesibilidad

- [ ] Botones micrófono y play: `aria-label` descriptivos ("Grabar narración", "Reproducir mensaje de {autor}")
- [ ] Feedback no solo visual: anuncio `aria-live` al iniciar/finalizar grabación y al completar transcripción
- [ ] TTS como alternativa a lectura — no sustituir texto en pantalla; subtítulos siempre visibles
- [ ] Atajos opcionales: Espacio para play/pause en mensaje enfocado (desktop)
- [ ] Respetar `prefers-reduced-motion` en animaciones de grabación

### Costes, API keys y operación

- [ ] Añadir a `.env.example`: `OPENAI_API_KEY` (STT+TTS OpenAI), `ELEVENLABS_API_KEY`, `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `STT_PROVIDER`, `TTS_PROVIDER`
- [ ] Documentar coste estimado por escena (minutos STT + caracteres TTS) en `docs/06_audio_features.md` — tabla comparativa proveedores
- [ ] Límites por campaña opcionales: `max_stt_minutes_per_scene`, `max_tts_chars_per_day` en `scene_state` o settings de campaña
- [ ] Logging de uso STT/TTS (usuario, bytes, duración, proveedor) para auditoría de costes — sin loguear contenido sensible en prod
- [ ] Desactivar features si no hay clave configurada: ocultar botones o mostrar tooltip "configurar API en servidor"

### Calidad y tests

- [ ] Tests backend: endpoint transcribe (mock OpenAI), endpoint TTS (mock), límites de tamaño y rate limit
- [ ] Tests frontend: `useAudioRecorder`, botón play en `ChatEntry`, estados de error de permisos
- [ ] Test manual checklist: grabar → transcribir → mensaje en chat → play TTS en desktop y móvil

---

## Resumen de brechas críticas docs ↔ código

| Documentado | Estado real |
|---|---|
| pgvector `campaign_memory` | ChromaDB en `rag.py` |
| `semantic_cache` | No existe |
| `scene_state` anidado (schema JSON) | Modelo plano en `scene.py` |
| Cierre de escena + WorldLog | Sin endpoint ni flujo |
| `@asistente` jugador | Sin endpoint ni UI |
| Rate limiting IA | Sin implementar |
| LLM Shadow Master | Stub hardcodeado |
| Capacitor APK | Sin Capacitor en el repo |
| Tests + CI | Ausentes |
| `docs/04` §7 "entities/auth no implementado" | **Desactualizado** — sí implementados |
