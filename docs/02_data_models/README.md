# Esquemas de Datos (`02_data_models/`)

Este directorio contiene los **contratos JSON Schema** (Draft 2020-12) que definen la estructura de todos los documentos dinámicos de campaña. Son la fuente de verdad para generar modelos Pydantic en `backend/app/schemas/`.

## Catálogo de esquemas

| Archivo | `title` | Tipo de entidad | Persistencia |
|---|---|---|---|
| `entity_npc_schema.json` | EntityNPC | NPC | `campaign_entities` |
| `entity_pc_schema.json` | EntityPC | Personaje jugador | `campaign_entities` |
| `entity_faction_schema.json` | EntityFaction | Facción / organización | `campaign_entities` |
| `entity_location_schema.json` | EntityLocation | Ubicación | `campaign_entities` |
| `relationship_schema.json` | Relationship | Vínculo entre entidades | `campaign_entities` |
| `arc_manifest_schema.json` | ArcManifest | Macrotrama (1 por campaña) | `campaign_entities` |
| `scene_state_schema.json` | SceneState | Estado de escena activa | `scenes.scene_state` |

## Convenciones

### Identificadores

- Cada **instancia** de entidad tiene un UUID en la columna `campaign_entities.id` (tabla SQL).
- Los campos `*_id` dentro de los documentos JSON referencian UUIDs de otras entidades de la misma campaña.
- El campo `$id` en cada archivo JSON Schema es el **identificador del esquema**, no de una instancia.

### Campos sensibles (solo Máster)

Estos campos **nunca** se exponen en respuestas API a jugadores:

- `ai_narrative_profile.secret_lore_master` (NPC)
- `narrative_profile.secret_lore_master` (Faction, Location)
- `narrative_bond.secret_nuance` (Relationship)
- `active_quests[].secret_dm_notes` (ArcManifest)

El backend debe filtrar estos campos según el rol del usuario autenticado.

### Agnosticismo de sistema de juego

Los bloques `system_mechanics` son contenedores genéricos (`system_name`, `stats_summary` como mapa clave-valor). El backend no interpreta reglas de ningún sistema concreto; solo almacena y valida.

### Validación

1. **Documentación:** JSON Schema en este directorio.
2. **Runtime:** Modelos Pydantic derivados manualmente (1 archivo por esquema).
3. **Regla:** Si el código y el schema divergen, el schema de `docs/` tiene prioridad.

### Ejemplos

Cada archivo incluye un array `examples` con una instancia válida de referencia. Úsalo para seeds de desarrollo y tests.

## Relaciones entre documentos

```
Campaign
├── ArcManifest (1 documento, entity_type=ARC_MANIFEST)
├── EntityLocation[] 
├── EntityFaction[]
├── EntityNPC[] ──────► referencian faction_id, current_location_id
├── EntityPC[] ───────► referencian user_id, current_location_id
├── Relationship[] ───► source_id / target_id apuntan a UUIDs de entidades
└── Scene[]
    └── scene_state (SceneState JSONB)
        ├── context.location_id → EntityLocation
        ├── context.active_npc_ids → EntityNPC[]
        ├── turn_management → EntityPC[]
        └── chat_buffer (mensajes inline, no entidad separada)
```

Ver `docs/04_data_persistence.md` para el modelo relacional completo.
