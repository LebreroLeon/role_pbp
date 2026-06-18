# D&D 5ª edición — manuales locales

Coloca aquí tus PDFs de reglas. **No se commitean** al repositorio.

## Core recomendado (MVP)

| Archivo sugerido | Contenido |
|---|---|
| `manual-del-jugador.pdf` | Player's Handbook / Manual del Jugador |
| `guia-dungeon-master.pdf` | Dungeon Master's Guide / Guía del DM |
| `manual-de-monstruos.pdf` | Monster Manual (opcional para combate/NPCs) |

## Copiar desde Descargas (Windows)

Si tienes la carpeta `C:\Users\lebre\Downloads\Dnd5\`:

```powershell
Copy-Item "C:\Users\lebre\Downloads\Dnd5\03D&D 5E - Manual del Jugador (Edge).pdf" `
  ".\manual-del-jugador.pdf"
Copy-Item "C:\Users\lebre\Downloads\Dnd5\01D&D 5E - Guía del Dungeon Master  (Edge).pdf" `
  ".\guia-dungeon-master.pdf"
Copy-Item "C:\Users\lebre\Downloads\Dnd5\02D&D 5E - Manual de Monstruos (Edge).pdf" `
  ".\manual-de-monstruos.pdf"
```

## Suplementos (opcional)

Xanathar, Tasha, Mordenkainen, Fizban, etc. — indexar solo si necesitas esas reglas en consultas IA; aumentan tiempo y coste de embeddings.

Tras copiar: `python backend/scripts/index_system_manuals.py --system dnd5e`
