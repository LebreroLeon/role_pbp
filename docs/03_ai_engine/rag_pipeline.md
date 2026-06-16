# 🧠 Arquitectura del Motor de IA: Canalización RAG (Rag Pipeline)

Este documento describe el flujo lógico que sigue el backend para enriquecer el contexto de los Modelos de Lenguaje (LLMs) mediante Generación Aumentada por Recuperación (RAG). El sistema equilibra el soporte creativo para el Máster ("Shadow Master") y la interacción controlada de los jugadores, optimizando el consumo de tokens mediante restricciones mecánicas y caché semántica.

## 1. El Flujo de Inyección de Contexto Híbrido (Paso a Paso)

Cuando se solicita explícitamente la interacción o consulta de la IA (y supera las reglas de validación de créditos), el sistema ejecuta este pipeline asíncrono en FastAPI:

    [ Solicitud de Interacción / Comando / Consulta ]
                        │
                        ▼
    =============================================
    0. Rate Limiting + Semantic Cache
       - Comprobar límite por campaña/usuario/rol
       - Buscar respuesta cacheada por similitud
       - Si hay hit → devolver sin llamar al LLM
    =============================================
                        │ (miss)
                        ▼
    =============================================
    1. Generación de Embeddings Semánticos
       - Se vectoriza la consulta del usuario
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
         facciones, ubicaciones y misiones
       - Si el emisor es JUGADOR: se purgan
         los campos secret_lore_master
    =============================================
                        │
                        ▼
    =============================================
    4. Construcción del Prompt (El Sándwich)
       - [Flags] + [RAG] + [Buffer] + [Input]
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

El volumen de datos inyectados se parametriza de forma estricta en la configuración de la escena (`memory_settings` en `scene_state_schema.json`):

* **`max_chat_buffer_size` (Ventana de Contexto Deslizable):** El backend acota el buffer inmediato de la escena (últimos 15-20 mensajes) para entender el flujo conversacional reciente.
* **`rag_top_k_matches` (Recuperación Histórica):** Fijado por defecto en `3`. Extrae únicamente los chunks más relevantes del pasado.
* **`max_player_lore_queries_per_scene`:** Pool máximo de consultas `@asistente` por escena (default `3`).

### Estructura de Prioridades del Prompt (El Sándwich)

La jerarquía de autoridad en la construcción del prompt asegura respuestas coherentes con el estado actual de la base de datos:

1. **ESTADO ABSOLUTO (PostgreSQL / JSONB):** Datos duros del presente. Si un NPC tiene `is_dead: true` o `is_present_in_scene: false`, la IA no puede interactuar con él físicamente en el presente.
2. **SECRETOS FILTRADOS:** Lore completo para el Máster; para jugadores se eliminan `secret_lore_master`, `secret_nuance` y `secret_dm_notes`.
3. **HISTORIAL SEMÁNTICO (RAG / pgvector):** Contexto narrativo indexado de escenas pasadas.
4. **BUFFER ACTIVO:** El hilo del chat reciente.

## 3. Rate Limiting (Protección de Créditos IA)

Las rutas que invocan el pipeline RAG o el LLM deben aplicar rate limiting **antes** de generar embeddings o llamar a APIs externas.

### Reglas por defecto (configurables por entorno)

| Endpoint / acción | Límite sugerido | Respuesta al exceder |
|---|---|---|
| Consulta Máster (`/master/assist`) | 10 req / minuto por `campaign_id` + `user_id` | `429 Too Many Requests` |
| Consulta jugador (`@asistente`) | Pool por escena (`remaining_player_lore_tokens`) | `429` + mensaje explicativo |
| Cierre de escena (`/scenes/{id}/close`) | 2 req / hora por `campaign_id` | `429` |
| Indexación de mensajes (background) | Sin límite LLM (no llama al LLM) | — |

### Sistema de créditos gamificado (jugadores)

* **Límite de escena:** Los jugadores comparten un pool cerrado (`max_player_lore_queries_per_scene`, default `3`), almacenado en `remaining_player_lore_tokens`.
* **Validación:** Cada consulta al `@asistente` resta 1 token. Al llegar a 0, FastAPI rechaza peticiones hasta el cierre de escena.
* **Excepción:** El Máster tiene consultas ilimitadas en su panel privado ("Shadow Master").

### Implementación

- Store en memoria para desarrollo; **Redis** o tabla PostgreSQL `rate_limit_buckets` para producción.
- Registrar intentos bloqueados en logs para detectar abuso.
- El chat narrativo normal no consume tokens ni llama al LLM.

## 4. Semantic Cache (Evitar Llamadas Redundantes al LLM)

Antes del paso 1 del pipeline, el backend comprueba si ya existe una respuesta válida para una consulta semánticamente similar en el mismo contexto de campaña.

### Clave de caché

```
cache_key = hash(
  campaign_id,
  query_embedding,
  state_snapshot_hash
)
```

El `state_snapshot_hash` se calcula a partir de flags críticos: NPCs activos, `is_dead`, misiones activas, `world_threat_level`, etc.

### Reglas de invalidación

- Cierre de escena en la campaña.
- Mutación de flags críticos en entidades.
- Edición manual de secretos del Máster.
- TTL expirado (24 h consultas creativas; 1 h con escena activa).

### Tabla de persistencia

Ver tabla `semantic_cache` en `docs/04_data_persistence.md`.

## 5. Almacenamiento Vectorial (pgvector)

Los embeddings se almacenan en la tabla `campaign_memory` de PostgreSQL con la extensión **pgvector**.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identificador del chunk |
| `campaign_id` | UUID | Aislamiento por campaña |
| `document_type` | enum | `CHAT_LOG`, `WORLDLOG`, `NPC_LORE`, `SCENE_SUMMARY` |
| `content` | TEXT | Texto plano indexado |
| `embedding` | vector(1536) | Dimensión según modelo de embeddings |
| `metadata` | JSONB | `scene_id`, `sender_id`, timestamps, etc. |

### Consulta de similitud

```sql
SELECT content, metadata
FROM campaign_memory
WHERE campaign_id = :campaign_id
ORDER BY embedding <=> :query_embedding
LIMIT :top_k;
```

El operador `<=>` es distancia coseno. Índice recomendado: **HNSW**.

## 6. Cierre de Escena y Mutación Automática de Estado

Al finalizar formalmente un bloque de juego:

1. **Consolidación del WorldLog:** La IA procesa el buffer del chat, genera un resumen ejecutivo y lo indexa vectorizado en pgvector.
2. **Sincronización Relacional:** El backend actualiza los documentos JSONB en `campaign_entities` (flags, misiones, actitudes).
3. **Reset de créditos:** Se restablece `remaining_player_lore_tokens` al valor de `max_player_lore_queries_per_scene`.
4. **Invalidación de caché:** Se purgan las entradas de `semantic_cache` de la campaña afectada.
