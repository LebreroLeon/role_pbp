# Fichas de personaje y combate automatizado

> Diseño arquitectónico para RolePBP. **Implementado en el código** (jun 2026): perfiles D&D 5e, Cyberpunk RED y VTM V5; fichas en `/ficha` y `/fichas`; combate con iniciativa y ataque; PBP con turnos. Este doc sigue siendo referencia de arquitectura; la sección 2 resume brechas menores pendientes.

---

## 1. Objetivos y alcance

| Objetivo | Descripción |
|---|---|
| Panel del jugador | Ruta dedicada para que cada jugador cree/edite **su** ficha (PC) vinculada a `player_binding.user_id`. |
| Fichas extensibles | Plantillas y validación por sistema: **D&D 5e**, **Cyberpunk RED**, **Vampiro: La Mascarada 5e** (MVP de sistemas). |
| Sistema al crear campaña | `CreateCampaignWizard` ya elige `game_system` → debe resolver **perfil de dados + plantilla de ficha + RuleEngine**. |
| Tiradas desde ficha | Botones/contexto (ataque, salvación, habilidad, etc.) que calculan modificadores y publican `DICE_ROLL` enriquecido. |
| Combate en escena | Iniciativa visible (PCs + NPCs), turnos de combate, daño aplicado a entidades. |
| Comandos en chat | `@npc ataca @jugador`, `/attack @origen to @destino` — parseo, tirada, daño, actualización de PV. |
| Permisos | Máster y jugadores pueden usar comandos de combate; jugadores solo editan su PC y tiran con sus entidades. |

**Fuera de alcance inicial (fases tardías):** mapas de batalla, línea de visión, hechizos completos D&D, ciberware detallado, disciplinas con árboles completos VTM, IA narrando combates.

---

## 2. Estado actual (brechas menores)

### Hecho

| Área | Estado |
|---|---|
| `backend/app/rules/` | Plugins `dnd5e`, `cyberpunk_red`, `vtm_v5` + `GenericFallbackPlugin` |
| Fichas UI | `CharacterSheetPage`, `CampaignSheetsPage`, formularios por sistema |
| Combate | `POST .../combat/initiative`, `.../combat/attack`; paneles en `ChatPage` |
| PBP | `pbp_enabled`, avance de turno, enforcement en backend |
| Tiradas enriquecidas | `DICE_ROLL` con `entity_id`, `roll_type`, `roll_details` |

### Pendiente menor

| Componente | Brecha |
|---|---|
| `ChatComposer` | Sin autocompletado `@` ni slash commands (`/attack`, `@npc ataca @pc`) |
| `DiceRoller` | Expresión manual; sin selector de habilidad desde ficha |
| WS combate | Paridad REST en acción `roll` / combate vía WebSocket |
| Formularios mundo | Creación de `FACTION`, `RELATIONSHIP`, `ARC_MANIFEST` limitada |
| Pulido | Tests E2E combate; bloqueo cambio `game_system` si hay fichas |

### Dependencias previas (ver `PENDING.md`)

`SceneState` anidado, `active_npc_ids`, cierre de escena y RAG pgvector ya están alineados. Prioridad restante: comandos de chat y pulido UX.

---

## 3. Arquitectura propuesta

### 3.1 Vista de capas

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (React)                                                 │
│  PlayerSheetPage ──► formularios por game_system (RHF + Zod)    │
│  CombatTracker (en ChatPage) ──► iniciativa, PV, turno actual   │
│  ChatComposer ──► @mentions, /commands, tiradas contextualizadas│
│  gameSystemProfiles.ts ◄── espejo de perfiles backend           │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST + WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│ API FastAPI                                                      │
│  entities.py ──► validación documento según system + rol        │
│  scenes.py ──► post_message ► CommandRouter (opcional)          │
│  combat.py ──► iniciativa, aplicar daño, avanzar turno          │
│  rolls.py ──► RollRequest ► RuleEngine.resolve_roll()           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ MOTOR DE REGLAS (Python)                                         │
│  RuleEngine (facade)                                             │
│    ├── GameSystemRegistry.get(campaign.game_system)              │
│    ├── plugins/dnd5e.py | cyberpunk_red.py | vtm_v5.py          │
│    └── DiceRoller (NdS, pools, percentil según perfil)         │
│  CombatResolver ──► ataque ► tirada ► daño ► mutación entidad   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ PostgreSQL JSONB                                                 │
│  campaign_entities.document ──► bloque system_mechanics tipado  │
│  scenes.scene_state ──► combat + turn_management ampliado       │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Principios de diseño

1. **Verdad en PostgreSQL:** PV, iniciativa y condiciones viven en entidades / `scene_state`, no en el chat. El chat registra el **historial** (mensajes `DICE_ROLL`, `COMBAT`, `SYSTEM`).
2. **Plugin por sistema:** cada `game_system` registra esquema de ficha, tipos de tirada, fórmulas y resolución de daño. El core no hardcodea D&D.
3. **Compatibilidad gradual:** entidades legacy con `stats_summary` plano siguen válidas; migración lazy al abrir editor de ficha.
4. **Un PC por jugador por campaña** (recomendado): enforced en `entities` service al crear PC.
5. **Menciones resuelven entidades**, no usuarios: `@Kaelen` → `campaign_entities.id` (PC o NPC por alias/nombre en escena).

### 3.3 Estructura de carpetas (objetivo)

```
backend/app/
  game_systems/
    __init__.py          # GameSystemRegistry
    base.py              # Protocol GameSystemPlugin, RollContext, RollResult
    dice.py              # ampliación de app/services/dice.py (mover/refactor)
    combat.py            # CombatResolver, DamageApplication
    plugins/
      dnd5e.py
      cyberpunk_red.py
      vtm_v5.py
  services/
    rolls.py             # orquestación API
    combat_scene.py      # iniciativa + turnos en scene_state
    chat_commands.py     # parser @ y /
  schemas/
    rolls.py
    combat.py
    game_systems/        # Pydantic por sistema (bloques system_mechanics)

frontend/src/
  features/
    character-sheet/
      PlayerSheetPage.tsx
      MasterSheetEditor.tsx   # edición NPC/PC por máster
      systems/
        dnd5e/
        cyberpunk_red/
        vtm_v5/
      useMyPcQuery.ts
    combat/
      CombatTracker.tsx
      InitiativePanel.tsx
    scene/
      ChatComposer.tsx        # + mention picker, command hints
      RollResultCard.tsx
  features/campaign/
    gameSystemProfiles.ts     # sheetTemplateId, diceMode, rollTypes
```

---

## 4. Modelo de datos por sistema

### 4.1 Evolución del esquema PC/NPC

Mantener el envoltorio agnóstico (`metadata`, `identity`, `player_binding`, `public_profile`, `state_flags`) y **reemplazar** el bloque genérico `system_mechanics` por una unión discriminada:

```json
"system_mechanics": {
  "system_id": "dnd5e",
  "schema_version": "1.0.0",
  "sheet": { /* campos específicos del sistema */ }
}
```

Los JSON Schema en `docs/02_data_models/` ganarán archivos hijo:

- `entity_pc_dnd5e_sheet.json`
- `entity_pc_cyberpunk_red_sheet.json`
- `entity_pc_vtm_v5_sheet.json`
- Análogos `entity_npc_*` (NPCs con bloque combat simplificado).

`metadata.system_agnostic` pasará a `false` para instancias con ficha mecánica completa (o un flag `mechanics_enabled: true`).

### 4.2 D&D 5ª edición (`dnd5e`)

**Categoría de dados:** d20 + modificador (`gameSystems.ts` → `d20`).

| Bloque | Campos clave |
|---|---|
| `abilities` | `str`, `dex`, `con`, `int`, `wis`, `cha` (2–20, modificador derivado) |
| `proficiency` | `bonus`, `saving_throws[]`, `skills[]` (nombre + proficient + expertise) |
| `defense` | `ac`, `hp: { max, current, temp }`, `hit_dice`, `death_saves` |
| `attacks[]` | `name`, `ability`, `proficient`, `damage: { dice, type }`, `properties[]` |
| `spellcasting` | (fase 2) `ability`, `slots`, `spells_known[]` |
| `conditions[]` | ids estándar 5e |
| `initiative` | `modifier` (normalmente DEX mod) |
| `inventory` | (fase 2) items con peso/propiedades |

**Tiradas soportadas (MVP):** ability check, saving throw, skill check, attack roll, damage roll, initiative.

**Daño:** suma de dados de arma + modificador (regla simplificada; resistencias en fase 2).

### 4.3 Cyberpunk RED (`cyberpunk_red`)

**Categoría:** pool de d10 (`dice_pool`).

| Bloque | Campos clave |
|---|---|
| `stats` | `int`, `ref`, `tech`, `cool`, `attr`, `luck`, `move`, `body`, `emp` |
| `skills[]` | `name`, `stat`, `rank` (0–10) |
| `role` | `name`, `ability` |
| `health` | `hp: { max, current }`, `seriously_wounded_threshold` |
| `armor` | `head`, `body` (SP) |
| `weapons[]` | `name`, `skill`, `damage`, `rof`, `autofire`, `armor_piercing` |
| `humanity` | `current`, `max` |
| `initiative` | `ref` + `combat_awareness` / mods |

**Tiradas:** skill check = pool de `stat + skill` d10s, **solo cuenta el dado más alto**; crítico si dos 10s (regla RED simplificada en MVP).

**Daño:** resta directa a HP; umbral herido grave cuando HP ≤ threshold.

### 4.4 Vampiro: La Mascarada 5e (`vtm_v5`)

**Categoría:** pool de d10 (`dice_pool`).

| Bloque | Campos clave |
|---|---|
| `attributes` | físicos `str/dex/sta`, sociales `cha/man/com`, mentales `int/wil/cer` (1–5) |
| `skills[]` | `name`, `category`, `dots` |
| `disciplines[]` | (fase 2) `name`, `level`, `powers[]` |
| `health` | `superficial`, `aggravated`, `max` (calculado: 3 + stamina) |
| `willpower` | `current`, `max` |
| `hunger` | 0–5 |
| `blood_potency` | 0–5 |
| `predator_type` | string |
| `weapons[]` | daño superficial/agravado |

**Tiradas:** pool = atributo + habilidad (+ disciplina); éxitos en 6+; 10 = dos éxitos; 1 en dados de hambre = posible bestia (flag narrativo MVP).

**Daño:** track dual superficial/agravado; conversión 2 superficial → 1 aggravated.

### 4.5 NPCs en combate

Misma estructura `system_mechanics.sheet` pero con subconjunto:

- PV/health, AC/armor, ataques básicos, iniciativa.
- Sin `player_binding`; el Máster edita desde Mundo o Mesa.

### 4.6 Extensión de `SceneState`

Añadir bloque `combat` (además de reutilizar `state_flags.conflict_mode_active`):

```json
"combat": {
  "is_active": true,
  "round": 1,
  "initiative_order": [
    {
      "entity_id": "uuid",
      "entity_type": "PC",
      "display_name": "Kaelen Vorr",
      "initiative_score": 17,
      "is_active": true
    }
  ],
  "current_turn_index": 0
}
```

`turn_management` existente sigue para **turnos narrativos** fuera de combate; cuando `combat.is_active`, la UI prioriza `combat.initiative_order`.

Nuevo tipo de mensaje en `chat_buffer`:

```json
{
  "type": "COMBAT",
  "text": "Goblin ataca a Kaelen: 18 vs CA 15 — impacto. 7 cortante.",
  "combat_event": {
    "kind": "ATTACK_RESOLVED",
    "attacker_id": "...",
    "defender_id": "...",
    "attack_roll": { "total": 18, "hit": true },
    "damage": { "amount": 7, "type": "slashing" }
  }
}
```

---

## 5. Motor de reglas abstracto (RuleEngine / GameSystem plugin)

### 5.1 Interfaz del plugin (`GameSystemPlugin`)

```python
class GameSystemPlugin(Protocol):
    system_id: str                    # "dnd5e"
    dice_mode: Literal["d20", "dice_pool", "d100"]
    sheet_schema_version: str

    def validate_pc_sheet(self, sheet: dict) -> BaseModel: ...
    def validate_npc_sheet(self, sheet: dict) -> BaseModel: ...

    def default_pc_sheet(self) -> dict: ...
    def default_npc_sheet(self, power_scale: str) -> dict: ...

    def resolve_roll(
        self,
        roll_type: str,               # "skill_check", "attack", "damage", ...
        actor_sheet: dict,
        context: RollContext,         # skill_id, target_ac, advantage, etc.
    ) -> RollResult: ...

    def resolve_attack(
        self,
        attacker_sheet: dict,
        defender_sheet: dict,
        weapon_or_attack_id: str,
        context: AttackContext,
    ) -> AttackResult: ...

    def apply_damage(
        self,
        defender_sheet: dict,
        damage: DamageResult,
    ) -> tuple[dict, DamageApplication]: ...  # sheet actualizado + resumen
```

### 5.2 Registro

```python
# backend/app/game_systems/__init__.py
REGISTRY: dict[str, GameSystemPlugin] = {
    "dnd5e": Dnd5ePlugin(),
    "cyberpunk_red": CyberpunkRedPlugin(),
    "vtm_v5": VtmV5Plugin(),
}

def get_game_system(campaign: Campaign) -> GameSystemPlugin:
    key = campaign.game_system or "generic"
    return REGISTRY.get(key, GenericFallbackPlugin())
```

`GenericFallbackPlugin`: comportamiento actual (`NdS+M`, sin daño automático).

### 5.3 `RollResult` unificado

```python
@dataclass
class RollResult:
    roll_type: str
    expression: str              # "1d20+5" o "7d10"
    rolls: list[int]             # dados individuales
    total: int | None            # d20: total; pool: éxitos o valor RED
    success: bool | None
    details: dict                # DC, skill, crítico, mensajes UI
    chat_summary: str            # texto humano para chat_buffer
```

### 5.4 Frontend: `gameSystemProfiles.ts`

Extiende `gameSystems.ts`:

```typescript
export type GameSystemProfile = GameSystem & {
  sheetTemplateId: string;
  supportedRollTypes: RollType[];
  combatEnabled: boolean;
  mentionPrefix: "@" | "/";
};
```

El wizard de campaña muestra preview: "D&D 5e — d20, ficha completa, combate automatizado".

---

## 6. Flujo de tiradas desde ficha

```
Jugador abre PlayerSheetPage
    → GET /campaigns/{id}/entities/mine (PC donde player_binding.user_id = yo)
    → UI renderiza formulario dnd5e | cyberpunk_red | vtm_v5

Clic "Tirar Percepción" (D&D)
    → POST /api/v1/scenes/{scene_id}/rolls
        { roll_type: "skill_check", entity_id, skill: "perception", dc?: 15 }
    → RuleEngine: lee sheet, calcula mod, tira d20
    → Append DICE_ROLL enriquecido a chat_buffer
    → WS broadcast scene_update

Alternativa in-scene (sin salir del chat):
    → Panel lateral "Acciones rápidas" con mismos endpoints
    → o comando: /roll perception dc 15
```

**Campos en `DICE_ROLL` ampliado** (retrocompatible):

| Campo | Uso |
|---|---|
| `entity_id` | Quién tiró (PC/NPC) |
| `roll_type` | `skill_check`, `attack`, etc. |
| `roll_details` | JSON con dados, DC, éxito |
| `skill_checked` | ya existe |

**Permisos:**

- Jugador: `entity_id` debe ser su PC (o NPC si el Máster delega — no MVP).
- Máster: cualquier entidad de la campaña presente en escena (`is_present_in_scene` o `active_npc_ids`).

---

## 7. Flujo de combate

### 7.1 Activar combate

1. Máster pulsa "Iniciar combate" en Mesa o Chat → `POST /scenes/{id}/combat/start`.
2. Backend recoge entidades presentes (`context.active_npc_ids` + PCs con `is_present_in_scene`).
3. Para cada una: tirada de iniciativa vía RuleEngine → rellena `combat.initiative_order`.
4. `state_flags.conflict_mode_active = true`, `combat.is_active = true`.
5. UI: `CombatTracker` junto al chat.

### 7.2 Comandos de chat

**Sintaxis MVP:**

| Comando | Ejemplo | Comportamiento |
|---|---|---|
| Mención natural | `@goblin ataca @kaelen` | Parser ES/EN: verbo ataca/attack → `CombatResolver` |
| Slash | `/attack @goblin to @kaelen` | Explícito; alias `->` |
| Slash arma | `/attack @kaelen longsword to @goblin` | Ataque con arma por id/nombre |
| Iniciativa | `/initiative` | Re-tira o añade entidad al combate |
| Daño manual | `/damage @goblin 8 slashing` | Máster aplica daño directo |
| Fin | `/combat end` | Desactiva combate |

**Pipeline en `post_message`:**

```
texto entrante
  → ChatCommandParser.try_parse(text)
  → si match combate:
       CombatResolver.execute(...)
       muta entidades (HP) + scene_state.combat
       append COMBAT + DICE_ROLL al buffer
  → si no match: flujo narrativo actual
```

**Resolución `@npc ataca @jugador`:**

1. Resolver menciones → `entity_id` (fuzzy match por `identity.name`, único en escena).
2. Validar combate activo (o auto-activar si Máster).
3. `RuleEngine.resolve_attack(atacante, defensor, arma_default)`.
4. Si impacto → `apply_damage` → persistir documento defensor.
5. Si HP ≤ 0 → flags (`is_incapacitated` PC, `is_dead` NPC).
6. Avanzar `current_turn_index` si el atacante era el turno actual (configurable).
7. Broadcast WS.

### 7.3 Orden de iniciativa en UI

```
┌─ Iniciativa (Ronda 2) ─────────────┐
│ ► Goblin Skulk     19  [NPC] 12/12│
│   Kaelen Vorr      17  [PC]  18/24│
│   Sister Mara      14  [PC]  22/22│
└────────────────────────────────────┘
```

- PV actuales leídos de `system_mechanics.sheet` (campo según sistema).
- Clic en entrada → ficha rápida / acciones.
- Máster: drag-and-drop reorder (opcional fase 3).

### 7.4 Integración con entidades vinculadas

| Escena | Entidad |
|---|---|
| `context.active_npc_ids[]` | NPCs elegibles en combate |
| PC con `state_flags.is_present_in_scene` | Elegibles |
| `player_binding.user_id` | Vincula jugador ↔ PC para panel y permisos |
| `@mention` | Resuelve contra entidades en escena + nombres de miembros (display_name → PC) |

Al aplicar daño, **`PUT /entities/{id}`** interno (servicio, no UI) actualiza solo el bloque `sheet` de salud — evita condiciones de carrera con edición manual de ficha (optimistic locking con `updated_at`).

---

## 8. Panel del jugador (frontend)

### 8.1 Ruta y navegación (jun 2026)

| Rol | Ruta | Nav | Descripción |
|---|---|---|---|
| **Jugador** | `/campaigns/:id/ficha` | Mi ficha | Crea/edita **solo su** PC (`PUT /campaigns/{id}/my-sheet`) |
| **Máster** | `/campaigns/:id/fichas` | Fichas | Lista todos los PCs (`GET /campaigns/{id}/sheets`, incluye secretos); edición completa vía `PUT /entities/{id}` |
| **Máster** | *(sin `/ficha`)* | — | El Máster no tiene "Mi ficha"; gestiona PJs desde **Fichas** |

- `CharacterSheetPage` protegida con `RoleGate role="PLAYER"`.
- `CampaignSheetsPage`: picker de PJs + `EntitySheetEditor` con vista Máster (stats, lore, secretos).
- Crear PJ para jugador sin ficha: botón opcional en Fichas (`POST /entities` con `buildPcDocumentForGameSystem`).

### 8.3 Separación Mundo vs Fichas (jun 2026)

| Vista | Quién | Contenido | API |
|---|---|---|---|
| **Fichas** (`CampaignSheetsPage`) | Solo Máster | Todos los **PCs**: narrativo + ficha mecánica + secretos | `GET /campaigns/{id}/sheets`, `PUT /entities/{id}` |
| **Mi ficha** (`CharacterSheetPage`) | Solo jugador | Su PC; tiradas desde formulario | `GET/PUT /campaigns/{id}/my-sheet`, `POST …/roll` |
| **Mundo** (`WorldPage`) | Máster: NPCs/ubicaciones; jugador: filtrado | Máster edita **NPCs** (lore + `secret_lore_master` + ficha mecánica D&D/RED/V5). Jugadores ven solo `public_description` y stats públicos (`strip_master_secrets` + NPCs ocultos en escena) | `GET /entities`, `PUT /entities/{id}` (Máster) |
| **Mesa** (`MasterDeskPage`) | Máster | Escena, jugadores, asistente — sin edición de fichas | — |

**Decisión UX:** PCs viven en **Fichas** (control total del Máster sobre jugadores). NPCs viven en **Mundo** (lore, presencia en escena, stats de combate). Evita duplicar la lista de entidades y mantiene el flujo narrativo del mundo separado de la gestión de mesa.

### 8.2 Edición

- React Hook Form + Zod por sistema (`Dnd5eSheetForm`, `CyberpunkSheetForm`, `VtmSheetForm`).
- Jugador: guardado explícito → `PUT /campaigns/{id}/my-sheet`.
- Máster: `EntitySheetEditor` compartido (Fichas + Mundo NPC) → `PUT /entities/{id}` con validación de plugin por `game_system`.
- Botones de tirada en ficha del jugador; escena activa recomendada para publicar en chat.

### 8.4 UX de combate (implementado jun 2026)

**Ficha del jugador** — tiradas sin objetivo:

- Atributos, salvaciones, habilidades, iniciativa y daño suelto desde botones en `Dnd5eSheetForm` / equivalentes.
- Endpoint: `POST /campaigns/{id}/my-sheet/roll` (cualquier miembro con PC; antes solo rol `PLAYER`).
- El ataque dirigido **no** se lanza desde la ficha; usar el chat.

**Chat — panel Combate rápido** (`QuickCombatActions.tsx`):

| Rol | Atacante | Objetivo | Arma |
|---|---|---|---|
| Jugador | Fijo: su PC | Selector: entidades en escena (no a sí mismo) | Dropdown `sheet.attacks[]` si hay varias |
| Máster | Selector: cualquier entidad en escena | Selector: otras entidades en escena | Igual |

- Ejecuta `POST /scenes/{id}/combat/attack` con `{ attacker_ref, defender_ref, weapon_name?, attack_index? }`.
- Resultado en chat como mensajes `COMBAT` + `DICE_ROLL` (`CombatEntry`).
- Menciones `@atacante ataca @objetivo` y `/attack …` siguen soportadas como atajo opcional.
- Errores WS (`event: error`) se muestran en `ChatPage` (antes se tragaban en silencio).

**Entidades en escena para combate:**

- PCs: `is_present_in_scene` **o** en `combat.initiative_order` **o** todos los PCs si aún no hay iniciativa.
- NPCs: `context.active_npc_ids` o en iniciativa.

---

## 9. API nueva (resumen)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/campaigns/{id}/entities/mine` | PC del usuario autenticado |
| POST | `/campaigns/{id}/entities/pc` | Crear PC con plantilla de sistema |
| POST | `/scenes/{id}/rolls` | Tirada contextualizada desde ficha |
| POST | `/scenes/{id}/combat/start` | Iniciativa + activar combate |
| POST | `/scenes/{id}/combat/end` | Desactivar combate |
| PATCH | `/scenes/{id}/combat/turn` | Avanzar / saltar turno |
| WS | `action: "roll"`, `action: "combat_command"` | Paridad REST |

---

## 10. Fases de implementación

### Fase 0 — Preparación (prerrequisitos)

- Alinear `SceneState` backend/frontend con schema anidado (`PENDING.md` § SceneState).
- Endpoint `GET /entities/mine` y `PUT /entities/{id}` en UI.
- Tests base para `dice.py` y validación de entidades.

### Fase 1 — Perfiles de sistema y plantillas

- `GameSystemRegistry` + `GenericFallbackPlugin`.
- JSON Schema + Pydantic para `dnd5e` sheet (PC mínimo viable: abilities, skills, hp, ac, 1 ataque).
- `gameSystemProfiles.ts` enlazado al wizard de campaña.
- Crear PC con plantilla al registrarse jugador o desde panel ficha.

### Fase 2 — Panel del jugador (D&D 5e primero)

- `PlayerSheetPage` + formulario D&D completo MVP.
- `POST /scenes/{id}/rolls` para skill check, saving throw, attack, damage.
- `DiceRoller` contextual en chat (selector de habilidad).
- Mensajes `DICE_ROLL` enriquecidos en UI (`RollResultCard`).

### Fase 3 — Combate e iniciativa

- Extensión `scene_state.combat` + migración.
- `CombatTracker` en `ChatPage`.
- `/attack`, `@ataca` parser + `CombatResolver` D&D.
- Aplicación automática de daño a `sheet.defense.hp`.
- Permisos Máster/jugador en comandos.

### Fase 4 — Cyberpunk RED

- Plugin RED + ficha (stats, skills, HP, armas).
- Pools d10 + regla del mayor dado.
- Combate con daño directo y umbral herido grave (UI badge).

### Fase 5 — Vampiro V5

- Plugin V5 + ficha (atributos, skills, health tracks, hunger).
- Pools con conteo de éxitos.
- Daño superficial/agravado.

### Fase 6 — Pulido

- Autocompletado `@` en `ChatComposer`.
- Reordenar iniciativa, condiciones, delegación Máster.
- Tests E2E: crear campaña D&D → ficha → escena → `/attack`.
- Documentar schemas hijo en `docs/02_data_models/`.

---

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Complejidad legal/reglas | MVP simplificado; textos "aproximación para mesa privada". |
| Divergencia schema ↔ Pydantic | Script de contrato tests (ya listado en `PENDING.md`). |
| Carrera edición ficha vs combate | Lock optimista `updated_at`; merge solo campos `health`. |
| `@mention` ambiguo | Desambiguar en UI; preferir entidades en escena. |
| `game_system` cambiado post-creación | Bloquear cambio si hay fichas mecánicas; o migración manual. |

---

## 12. Referencias internas

- `frontend/src/features/campaign/gameSystems.ts` — catálogo actual
- `docs/02_data_models/entity_pc_schema.json` — contrato PC vigente
- `docs/02_data_models/scene_state_schema.json` — `conflict_mode_active`, `turn_management`
- `backend/app/services/dice.py` — parser actual
- `backend/app/services/scenes.py` — chat y tiradas sin reglas
- `PENDING.md` — ítems accionables derivados de este documento
