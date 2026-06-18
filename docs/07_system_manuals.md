# Manuales de sistema (reglas oficiales por juego)

> Diseño arquitectónico — **no implementado**. Objetivo: que Shadow Master, `@asistente` y el consultor de reglas puedan citar reglas oficiales del sistema de la campaña (D&D 5e, VTM V5, Cyberpunk RED, etc.) sin mezclar manuales entre sistemas.

Detalle de tareas accionables: `PENDING.md` § Manuales de sistema.

---

## 1. Problema y alcance

| Fuente actual | Qué indexa | Limitación |
|---|---|---|
| `campaign_documents` + `campaign_uploads/` | PDFs/notas **por campaña** (módulos, homebrew) | No hay manuales globales reutilizables entre campañas |
| `campaign_memory` (pgvector) | Chat, WorldLog, lore NPC | Solo memoria narrativa; sin reglas oficiales |
| `backend/app/rules/{system_id}/` | Validación mecánica (tiradas, fichas) | Lógica hardcodeada, no texto del manual |

Los manuales oficiales son **compartidos por sistema**, no por campaña. Una campaña D&D 5e debe consultar el *Manual del Jugador*; una campaña VTM debe consultar el *Corebook*, nunca al revés.

**Fuera de alcance (MVP):** OCR de escaneos de baja calidad, traducción automática, edición de PDFs, distribución de PDFs con el repo.

---

## 2. Ubicación de archivos en disco

### Decisión: `data/manuals/{system_id}/`

| Opción | Pros | Contras |
|---|---|---|
| `backend/manuals/` | Cerca del script de indexación | Mezcla binarios con código Python |
| **`data/manuals/`** ✓ | Paralelo a `campaign_uploads/`; gitignore claro | Ruta adicional en config |

Los PDFs **no se commitean** (copyright). Solo se versionan READMEs de plantilla y metadatos de ejemplo.

```
role_pbp/
├── data/
│   └── manuals/
│       ├── README.md                 ← instrucciones generales (versionado)
│       ├── dnd5e/
│       │   ├── README.md             ← qué copiar aquí (versionado)
│       │   └── *.pdf                 ← gitignored
│       ├── vtm_v5/
│       │   └── README.md
│       └── cyberpunk_red/
│           └── README.md
├── campaign_uploads/                 ← ya existe; material por campaña
└── backend/scripts/
    └── index_system_manuals.py       ← indexador (stub)
```

### Variable de entorno

```env
SYSTEM_MANUALS_DIR=data/manuals   # ruta relativa al repo o absoluta
```

En Docker: montar volumen `./data/manuals:/app/data/manuals:ro`.

---

## 3. Copiar manuales localmente (sin automatizar)

**No copiar PDFs al repo desde el agente ni en CI.** Cada desarrollador/Máster los coloca a mano.

### Windows (PowerShell) — ejemplo D&D 5e

```powershell
# Crear destino si no existe
New-Item -ItemType Directory -Force -Path "C:\Users\lebre\Projects\role_pbp\data\manuals\dnd5e"

# Copiar uno o todos desde Descargas (ajustar nombres si difieren)
Copy-Item "C:\Users\lebre\Downloads\Dnd5\03D&D 5E - Manual del Jugador (Edge).pdf" `
  "C:\Users\lebre\Projects\role_pbp\data\manuals\dnd5e\manual-del-jugador.pdf"

# O copiar la carpeta entera renombrando archivos después si se desea
# Copy-Item "C:\Users\lebre\Downloads\Dnd5\*.pdf" "...\data\manuals\dnd5e\"
```

Convención de nombres sugerida: `kebab-case` en ASCII (`manual-del-jugador.pdf`, `guia-dungeon-master.pdf`) para evitar problemas de encoding en Linux/Docker.

### Verificar antes de indexar

```powershell
Get-ChildItem "C:\Users\lebre\Projects\role_pbp\data\manuals\dnd5e" -Filter *.pdf
```

---

## 4. `.gitignore`

Añadir al `.gitignore` del repo:

```gitignore
# Manuales oficiales (copyright — solo local / volumen Docker)
data/manuals/**/*.pdf
data/manuals/**/*.PDF
```

Así se commitean los README de plantilla; los PDFs permanecen locales.

---

## 5. Modelo de datos

### 5.1 Inventario: `system_manual_sources`

Registro de cada PDF detectado en disco (no el contenido vectorizado).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `system_id` | VARCHAR(64) | `dnd5e`, `vtm_v5`, `cyberpunk_red` — alineado con `campaigns.game_system` |
| `filename` | VARCHAR(255) | Nombre en disco |
| `title` | VARCHAR(255) | Título legible (opcional, desde README o frontmatter) |
| `sha256` | CHAR(64) | Hash del archivo; detectar cambios para re-indexar |
| `size_bytes` | BIGINT | |
| `page_count` | INT | Tras extracción |
| `index_status` | ENUM | `PENDING`, `INDEXING`, `INDEXED`, `FAILED` |
| `indexed_at` | TIMESTAMPTZ | |
| `error_message` | TEXT | Si `FAILED` |
| `metadata` | JSONB | `language`, `edition`, `is_core`, etc. |

Índice único: `(system_id, filename)`.

### 5.2 Chunks vectoriales: `system_manual_memory`

Paralela a `campaign_memory`, pero scoped por **sistema**, no por campaña.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK del chunk |
| `system_id` | VARCHAR(64) | Filtro principal en RAG |
| `source_id` | UUID FK | → `system_manual_sources.id` |
| `content` | TEXT | Texto del chunk |
| `embedding` | vector(1536) | Mismo modelo que `campaign_memory` |
| `metadata` | JSONB | `page`, `section`, `chunk_index`, `source_filename` |
| `created_at` | TIMESTAMPTZ | |

Índice HNSW sobre `embedding`. Índice B-tree en `(system_id)`.

**Alternativa (no recomendada):** extender `campaign_memory` con `campaign_id` nullable y `document_type=SYSTEM_MANUAL`. Mezcla responsabilidades y complica FKs; preferir tabla dedicada.

### 5.3 Extender enum `memory_document_type` (opcional)

Si más adelante se unifican tablas, añadir `SYSTEM_MANUAL` al enum documentado en `docs/04_data_persistence.md`. Con tabla separada no es necesario en MVP.

---

## 6. Pipeline de indexación

```
PDF en data/manuals/{system_id}/
        │
        ▼
┌───────────────────────────┐
│ index_system_manuals.py   │  ← CLI: --system dnd5e [--force]
│ (o job POST /admin/...)   │
└───────────────────────────┘
        │
        ├─► Calcular sha256; upsert system_manual_sources
        │
        ├─► Extraer texto (pymupdf / pdfplumber)
        │     • por página, preservar número de página en metadata
        │
        ├─► Chunking (~500–800 tokens, solapamiento 80–100)
        │     • respetar saltos de sección cuando sea posible
        │
        ├─► Embeddings (OpenAI text-embedding-3-small)
        │
        └─► INSERT system_manual_memory
              • borrar chunks previos del mismo source_id si sha256 cambió
              • marcar source INDEXED / FAILED
```

### Dependencias Python (futuro)

- `pymupdf` o `pdfplumber` — extracción
- Cliente embeddings ya presente en `backend/app/services/rag.py`

### Idempotencia

- Mismo `sha256` → skip (salvo `--force`).
- PDF modificado → delete chunks by `source_id`, re-indexar.

---

## 7. Integración RAG (Shadow Master / @asistente / reglas)

### Flujo en consulta

Cuando `build_master_assist_response` (o futuro `@asistente`) ejecuta búsqueda vectorial:

1. Leer `campaign.game_system` (ej. `dnd5e`).
2. **Consulta A — memoria de campaña** (existente):

```sql
SELECT content, metadata
FROM campaign_memory
WHERE campaign_id = :campaign_id
ORDER BY embedding <=> :query_embedding
LIMIT :k_campaign;
```

3. **Consulta B — manuales del sistema**:

```sql
SELECT content, metadata
FROM system_manual_memory
WHERE system_id = :game_system
ORDER BY embedding <=> :query_embedding
LIMIT :k_manual;
```

4. **Fusión en el Sándwich** (`docs/03_ai_engine/rag_pipeline.md`):

```
[Flags estado JSONB]
+ [RAG campaña — top k_campaign]
+ [RAG manuales sistema — top k_manual]   ← nuevo bloque
+ [Buffer chat]
+ [Consulta usuario]
```

Parámetros sugeridos en `memory_settings` (futuro):

| Clave | Default | Descripción |
|---|---|---|
| `rag_top_k_matches` | 3 | Chunks de campaña (ya documentado) |
| `rag_manual_top_k` | 2 | Chunks de manual del sistema |
| `rag_include_manuals` | true | Máster: sí; jugador: solo si campaña lo permite |

### Filtrado estricto

- Campaña `dnd5e` → **solo** `system_id = 'dnd5e'`. Nunca mezclar VTM/Cyberpunk.
- Si `game_system` es null → omitir consulta B; log warning.
- Documentos de `campaign_documents` (biblioteca de campaña) siguen siendo un tercer bucket opcional (`document_type=CAMPAIGN_DOC` en memoria de campaña).

### Roles

| Rol | Manuales sistema | Secretos campaña | Pool @asistente |
|---|---|---|---|
| Máster (Shadow Master) | ✓ | ✓ | Ilimitado |
| Jugador (@asistente) | ✓ (reglas públicas) | ✗ | `remaining_player_lore_tokens` |

Para jugadores, el prompt de reglas debe indicar: *citar reglas generales del manual, no secretos de campaña*.

---

## 8. API (futuro)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/systems/{system_id}/manuals` | Lista `system_manual_sources` + estado indexación |
| `POST` | `/api/v1/admin/manuals/reindex` | Dispara indexación (solo admin / dev) |
| `GET` | `/api/v1/campaigns/{id}/manuals/availability` | Manuales del `game_system` de la campaña |

No hay upload HTTP de manuales en MVP: se añaden por filesystem + script.

---

## 9. UI — «Manuales del sistema»

Sección **solo lectura** en:

- **Biblioteca** (`LibraryPage.tsx`) — pestaña o bloque inferior «Manuales del sistema», o
- **Mesa del Máster** (`MasterDeskPage.tsx`) — subsección en pestaña Campaña / Asistente

### Contenido

- Lista de PDFs esperados para `campaign.game_system` (desde API `system_manual_sources`).
- Estado por archivo: `No encontrado` | `Pendiente` | `Indexado` (fecha) | `Error`.
- Badge global: «Reglas D&D 5e disponibles para la IA» (verde si ≥1 core indexado).
- **Sin** descarga ni upload desde UI (evitar servir PDFs con copyright desde producción).
- Tooltip: «Coloca los PDFs en `data/manuals/{system_id}/` en el servidor y ejecuta el indexador».

Los `campaign_documents` existentes siguen siendo material **de campaña** (aventuras, notas); los manuales de sistema son capa separada.

---

## 10. `system_id` canónicos

Alineados con `backend/app/rules/game_systems.py`:

| system_id | Etiqueta | Carpeta |
|---|---|---|
| `dnd5e` | D&D 5ª edición | `data/manuals/dnd5e/` |
| `vtm_v5` | Vampiro: La Mascarada V5 | `data/manuals/vtm_v5/` |
| `cyberpunk_red` | Cyberpunk RED | `data/manuals/cyberpunk_red/` |

Nuevos sistemas: añadir perfil en `game_systems.py`, carpeta bajo `data/manuals/`, README template.

---

## 11. Inventario D&D 5e detectado (referencia local del usuario)

En `C:\Users\lebre\Downloads\Dnd5\` (11 PDFs, ~1,9 GB total):

| Archivo | Tamaño aprox. |
|---|---|
| 01D&D 5E - Guía del Dungeon Master (Edge).pdf | 95 MB |
| 02D&D 5E - Manual de Monstruos (Edge).pdf | 98 MB |
| 03D&D 5E - Manual del Jugador (Edge).pdf | 83 MB |
| 04Guía de Monstruos de Volo.pdf | 14 MB |
| 05Guia de Xanathar Para Todo.pdf | 29 MB |
| 06Caldero de Tasha para Todo.pdf | 27 MB |
| 07Tomo de Enemigos de Mordenkainen HD.pdf | 396 MB |
| 08Mordenakinen presenta Monstruos del Multiverso.pdf | 34 MB |
| 09El Tesoro de los Dragones de Fizban.pdf | 219 MB |
| Guía del aventurero de la Costa de la Espada.pdf | 114 MB |
| Volos Waterdeep Enchiridion.pdf | 3 MB |

**MVP recomendado para indexar primero:** Manual del Jugador + Guía del DM (core). Suplementos bajo demanda.

---

## 12. Relación con otros documentos

| Doc | Relación |
|---|---|
| `docs/03_ai_engine/rag_pipeline.md` | Añadir paso 2b (búsqueda manuales por `system_id`) |
| `docs/04_data_persistence.md` | Documentar tablas `system_manual_*` |
| `PENDING.md` | Tareas de implementación |
| `campaign_uploads/` | Material narrativo por campaña, no manuales globales |
