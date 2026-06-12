```markdown
# 🗺️ Esquema de Datos: Grafo de Relaciones (`Relationship`)

El sistema utiliza este modelo de datos para construir un mapa dinámico de conexiones semánticas. Esto permite a la IA comprender los vínculos de lealtad, odio, deudas o secretos entre cualquier entidad (Jugadores y NPCs) de la campaña.

## 1. Estructura JSON Universal

```json
{
  "$id": "rel_001",
  "metadata": {
    "type": "RELATIONSHIP",
    "created_at": "2026-06-12T17:00:00Z",
    "last_updated": "2026-06-12T17:00:00Z"
  },
  "connection": {
    "source_id": "entity_npc_001", 
    "target_id": "char_player_04", 
    "is_bidirectional": false
  },
  "narrative_bond": {
    "bond_type": "Deuda de Vida / Chantaje / Rivalidad",
    "public_status": "Aparentan ser socios comerciales legítimos ante el resto del grupo.",
    "secret_nuance": "El target_id descubrió que el source_id es un informante infiltrado. Ahora lo chantajea para obtener pases de seguridad.",
    "tension_level": 8
  },
  "ai_behavior_guidelines": {
    "if_source_acts": "Debe mostrarse sumiso y nervioso cuando el target esté presente en la escena.",
    "if_target_acts": "Puede usar sutiles amenazas veladas en el chat de juego para recordar su posición de poder."
  },
  "state_flags": {
    "is_secret_discovered_by_party": false,
    "is_active": true
  }
}
