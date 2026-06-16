# 💾 Modelo de Persistencia de Datos

Este documento define cómo se almacenan las entidades narrativas y la memoria vectorial en PostgreSQL. Complementa los JSON Schema de `docs/02_data_models/`.

## 1. Principio de diseño

RolePBP usa un modelo **híbrido**:

| Tipo de dato | Almacenamiento | Motivo |
|---|---|---|
| Entidades de campaña (NPC, PC, Facción…) | Tabla `campaign_entities` con documento JSONB validado | Flexible, agnóstico, consultable por ID |
| Estado de escena activa (turnos, buffer) | Columna `scenes.scene_state` JSONB | Alta frecuencia de escritura, un doc por escena |
| Memoria narrativa (RAG) | Tabla `campaign_memory` con pgvector | Búsqueda por similitud semántica |
| Caché de respuestas IA | Tabla `semantic_cache` | Evitar llamadas redundantes al LLM |
| Metadatos de campaña | Tabla `campaigns` relacional | Consultas simples, listados |

**Regla:** PostgreSQL JSONB es la verdad absoluta del presente. pgvector es memoria histórica; nunca sobrescribe flags de estado.

## 2. Diagrama de tablas

```
campaigns
├── id (UUID, PK)
├── name, tone, created_at
│
├── campaign_members (M:N usuarios ↔ campañas)
│   ├── campaign_id, user_id
│   └── role: MASTER | PLAYER
│
├── campaign_entities (documentos JSONB tipados)
│   ├── id (UUID, PK)          ← ID referenciado en los JSON
│   ├── campaign_id (FK)
│   ├── entity_type (enum)     ← NPC | PC | FACTION | LOCATION | RELATIONSHIP | ARC_MANIFEST
│   ├── document (JSONB)       ← validado contra JSON Schema
│   └── updated_at
│
├── scenes
│   ├── id (UUID, PK)
│   ├── campaign_id (FK)
│   ├── status
│   ├── scene_state (JSONB)    ← SceneState schema
│   └── created_at, updated_at
│
├── campaign_memory (pgvector)
│   ├── id (UUID, PK)
│   ├── campaign_id (FK)
│   ├── document_type (enum)
│   ├── content (TEXT)
│   ├── embedding (vector)
│   └── metadata (JSONB)
│
└── semantic_cache
    ├── id (UUID, PK)
    ├── campaign_id (FK)
    ├── state_snapshot_hash (TEXT)
    ├── query_embedding (vector)
    ├── response_payload (JSONB)
    └── expires_at
```

## 3. Tablas en detalle

### `campaigns`

Metadatos de alto nivel. Una fila por campaña.

```sql
CREATE TABLE campaigns (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(200) NOT NULL,
    tone        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### `campaign_members`

Vincula usuarios autenticados a campañas con rol.

```sql
CREATE TYPE member_role AS ENUM ('MASTER', 'PLAYER');

CREATE TABLE campaign_members (
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL,
    role        member_role NOT NULL,
    PRIMARY KEY (campaign_id, user_id)
);
```

### `campaign_entities`

Almacena todos los documentos JSON de entidades narrativas. El UUID de la fila es el que se usa en referencias cruzadas (`faction_id`, `source_id`, etc.).

```sql
CREATE TYPE entity_type AS ENUM (
    'NPC', 'PC', 'FACTION', 'LOCATION', 'RELATIONSHIP', 'ARC_MANIFEST'
);

CREATE TABLE campaign_entities (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    entity_type entity_type NOT NULL,
    document    JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_entities_campaign_type ON campaign_entities (campaign_id, entity_type);
CREATE INDEX idx_entities_document ON campaign_entities USING GIN (document);
```

**Flujo de escritura:** el backend valida `document` con Pydantic → `INSERT` o `UPDATE`. En cierre de escena, se mutan los flags dentro de `document` y se actualiza `updated_at`.

### `scenes`

```sql
CREATE TABLE scenes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    status      VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    scene_state JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

El `chat_buffer` vive **dentro** de `scene_state`, no en tabla separada. Al superar `max_chat_buffer_size`, los mensajes más antiguos se archivan: se indexan en `campaign_memory` (pgvector) y se eliminan del buffer.

### `campaign_memory` (pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE memory_document_type AS ENUM (
    'CHAT_LOG', 'WORLDLOG', 'NPC_LORE', 'SCENE_SUMMARY'
);

CREATE TABLE campaign_memory (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id   UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    document_type memory_document_type NOT NULL,
    content       TEXT NOT NULL,
    embedding     vector(1536) NOT NULL,
    metadata      JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_memory_campaign ON campaign_memory (campaign_id);
CREATE INDEX idx_memory_embedding ON campaign_memory
    USING hnsw (embedding vector_cosine_ops);
```

La dimensión `1536` corresponde a `text-embedding-3-small` de OpenAI. Configurable vía variable de entorno.

### `semantic_cache`

```sql
CREATE TABLE semantic_cache (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id          UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    state_snapshot_hash  TEXT NOT NULL,
    query_embedding      vector(1536) NOT NULL,
    response_payload     JSONB NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at           TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_cache_campaign ON semantic_cache (campaign_id);
```

## 4. Consultas típicas del pipeline RAG

### Cargar estado absoluto para el Sándwich de contexto

```sql
-- NPCs activos en escena
SELECT e.id, e.document
FROM campaign_entities e
WHERE e.campaign_id = :campaign_id
  AND e.entity_type = 'NPC'
  AND (e.document->'state_flags'->>'is_present_in_scene')::boolean = true;

-- Arco manifest (1 por campaña)
SELECT document FROM campaign_entities
WHERE campaign_id = :campaign_id AND entity_type = 'ARC_MANIFEST'
LIMIT 1;
```

### Búsqueda vectorial

```sql
SELECT content, metadata
FROM campaign_memory
WHERE campaign_id = :campaign_id
ORDER BY embedding <=> :query_embedding
LIMIT :top_k;
```

## 5. Filtrado de campos sensibles por rol

Al serializar `campaign_entities.document` para la API:

| Rol | Campos visibles |
|---|---|
| PLAYER | `public_description`, `public_profile`, `public_status`, `identity.name` |
| MASTER | Documento completo incluyendo todos los `secret_*` y `secret_dm_notes` |

La lógica de filtrado vive en `backend/app/services/` (capa de servicio), no en las rutas.

## 6. Migración desde ChromaDB (prototipo actual)

El archivo `backend/app/services/rag.py` usa ChromaDB como prototipo del Día 1. La implementación objetivo reemplaza ChromaDB por consultas a `campaign_memory` con pgvector. Pasos:

1. Imagen Docker `pgvector/pgvector:pg16` (ya configurada en `docker-compose.yml`).
2. Crear extensión y tablas en migración Alembic.
3. Reescribir `RagService` para usar SQLAlchemy + pgvector.
4. Eliminar dependencia `chromadb` de `requirements.txt`.

## 7. Estado actual del código vs. modelo objetivo

| Componente | Estado actual | Objetivo documentado |
|---|---|---|
| `campaigns` + `scenes` | Implementado (SQLAlchemy) | Alineado |
| `campaign_entities` | No implementado | Pendiente |
| `campaign_members` / auth | No implementado | Pendiente |
| `campaign_memory` (pgvector) | No implementado | Pendiente |
| `semantic_cache` | No implementado | Pendiente |
| RAG (ChromaDB) | Prototipo funcional | Migrar a pgvector |
