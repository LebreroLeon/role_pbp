# 🧠 Arquitectura del Motor de IA: Canalización RAG (Rag Pipeline)

Este documento describe el flujo lógico que sigue el backend para enriquecer el contexto de los Modelos de Lenguaje (LLMs) mediante Generación Aumentada por Recuperación (RAG). En este modelo, el motor de IA actúa exclusivamente como soporte privado para el Máster ("Shadow Master") y gestor del historial automatizado, eliminando interacciones directas con jugadores para optimizar costes y garantizar la seguridad del lore.

## 1. El Flujo de Inyección de Contexto del Máster (Paso a Paso)

Cuando el Máster solicita asistencia en su panel privado (ej: consulta de intenciones de un NPC, ganchos de escena o verificación de datos del diario), el sistema ejecuta este pipeline asíncrono en FastAPI:

    [ Solicitud Explícita del Máster / Botón de Panel ]
                        │
                        ▼
    =============================================
    0. Rate Limiting + Semantic Cache
       - Comprobar límite por campaña/usuario
       - Buscar respuesta cacheada por similitud
       - Si hay hit → devolver sin llamar al LLM
    =============================================
                        │ (miss)
                        ▼
    =============================================
    1. Generación de Embeddings Semánticos
       - Se vectoriza la consulta del Máster
    =============================================
                        │
                        ▼
    =============================================
    2. Consulta Vectorial (pgvector en PostgreSQL)
       - Búsqueda de similitud coseno
       - Top-K chunks del historial y resúmenes
    =============================================
                        │
                        ▼
    =============================================
    3. Extracción de Estado Completo (Postgres JSONB)
       - Se inyecta el JSON actual de NPCs, PCs,
         facciones, ubicaciones, misiones y secretos
    =============================================
                        │
                        ▼
    =============================================
    4. Construcción del Prompt (El Sándwich)
       - [Flags/Secretos] + [RAG] + [Buffer] + [Input]
    =============================================
                        │
                        ▼
            [ Envío a la API del LLM ]
                        │
                        ▼
    =============================================
    5. Persistir en Semantic Cache
       - Guardar respuesta con hash de estado
    =============================================

## 2. Gestión de Memoria Operativa y Configuración

El volumen de datos inyectados se parametriza de forma estricta en la configuración global de la campaña (`memory_settings` en `scene_state_schema.json`) para mitigar el ruido en el modelo:

* **`max_chat_buffer_size` (Ventana de Contexto Deslizable):** El backend acota el buffer inmediato de la escena (últimos 15-20 mensajes de los jugadores). El LLM solo lee esto para entender el "aquí y ahora" del roleo antes de sugerirle una respuesta al Máster.
* **`rag_top_k_matches` (Recuperación Histórica):** Fijado por defecto en `3`. Extrae únicamente los chunks más relevantes del pasado. Al estar limitado al Máster, estos chunks incluyen eventos globales que los jugadores pueden desconocer.

### Estructura de Prioridades del Prompt (El Sándwich del Máster)

La jerarquía de autoridad en la construcción del prompt asegura sugerencias coherentes con el estado actual de la base de datos:

1.  **ESTADO ABSOLUTO (PostgreSQL / JSONB):** Datos duros del presente. Si un NPC tiene el flag `is_dead: true` o `is_present_in_scene: false`, el prompt instruye a la IA a vetar cualquier acción física de dicho personaje, utilizándolo únicamente como referencia histórica.
2.  **SECRETOS Y LORE COMPLETO:** Información oculta del panel del Máster (`secret_lore_master`, `secret_dm_notes`, `secret_nuance`). La IA cruza estos datos con el estado del mundo para diseñar giros dramáticos o revelar pistas de forma controlada.
3.  **HISTORIAL SEMÁNTICO (RAG / pgvector):** Contexto narrativo indexado de las escenas pasadas.
4.  **BUFFER ACTIVO:** El flujo conversacional reciente de los jugadores.

## 3. Rate Limiting (Protección de Créditos IA)

Las rutas que invocan el pipeline RAG o el LLM deben aplicar rate limiting **antes** de generar embeddings o llamar a APIs externas.

### Reglas por defecto (configurables por entorno)

| Endpoint / acción | Límite sugerido | Respuesta al exceder |
|---|---|---|
| Consulta Máster (`/master/assist`) | 10 req / minuto por `campaign_id` + `user_id` | `429 Too Many Requests` |
| Cierre de escena (`/scenes/{id}/close`) | 2 req / hora por `campaign_id` | `429` + mensaje explicativo |
| Indexación de mensajes (background) | Sin límite LLM (no llama al LLM) | — |

### Implementación

- Usar un store en memoria para desarrollo; **Redis** o tabla PostgreSQL `rate_limit_buckets` para producción.
- Registrar intentos bloqueados en logs para detectar abuso.
- El rate limit no aplica al chat de jugadores (fase cero-token).

## 4. Semantic Cache (Evitar Llamadas Redundantes al LLM)

Antes del paso 1 del pipeline, el backend comprueba si ya existe una respuesta válida para una consulta semánticamente similar en el mismo contexto de campaña.

### Clave de caché

```
cache_key = hash(
  campaign_id,
  query_embedding,          # vector de la consulta del Máster
  state_snapshot_hash       # hash de flags críticos de PostgreSQL
)
```

El `state_snapshot_hash` se calcula a partir de los flags duros que afectan la respuesta: NPCs activos en escena, `is_dead`, misiones activas, `world_threat_level`, etc.

### Reglas de invalidación

La caché se invalida (o se ignora) cuando ocurre cualquiera de estos eventos:

- Cierre de escena en la campaña.
- Mutación de flags críticos en entidades (`is_dead`, `is_present_in_scene`, `is_active` en relaciones).
- El Máster edita manualmente `secret_lore_master` o notas de misión.
- TTL expirado (sugerido: 24 h para consultas creativas, 1 h si hay escena activa con alta actividad).

### Tabla de persistencia

Ver tabla `semantic_cache` en `docs/04_data_persistence.md`.

### Beneficio esperado

Consultas repetidas del Máster del tipo *"¿Qué haría este NPC ahora?"* con el mismo estado de mundo devuelven la respuesta cacheada con **coste cero de tokens**.

## 5. Almacenamiento Vectorial (pgvector)

Los embeddings se almacenan en la tabla `campaign_memory` de PostgreSQL con la extensión **pgvector**.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identificador del chunk |
| `campaign_id` | UUID | Aislamiento por campaña |
| `document_type` | enum | `CHAT_LOG`, `WORLDLOG`, `NPC_LORE`, `SCENE_SUMMARY` |
| `content` | TEXT | Texto plano indexado |
| `embedding` | vector(1536) | Dimensión según modelo de embeddings (configurable) |
| `metadata` | JSONB | `scene_id`, `sender_id`, timestamps, etc. |

### Consulta de similitud

```sql
SELECT content, metadata
FROM campaign_memory
WHERE campaign_id = :campaign_id
ORDER BY embedding <=> :query_embedding
LIMIT :top_k;
```

El operador `<=>` es distancia coseno en pgvector. El índice recomendado es **HNSW** para campañas con historial largo.

## 6. Cierre de Escena y Mutación Automática de Estado

El mayor consumo automatizado de tokens ocurre de forma controlada únicamente al finalizar un bloque de juego:

1.  **Consolidación del WorldLog:** Al activar el "Cierre de Escena", la IA procesa el buffer completo del chat, genera un resumen ejecutivo de los acontecimientos y lo indexa vectorizado en pgvector.
2.  **Sincronización Relacional:** El backend analiza el desenlace para actualizar los documentos JSONB en PostgreSQL (`UPDATE` en `campaign_entities`). Si el transcurso de la escena alteró flags de salud, estados de misiones o la actitud de una facción, el cambio queda consolidado de inmediato para la siguiente sesión.
3.  **Invalidación de caché:** Se purgan las entradas de `semantic_cache` de la campaña afectada.
