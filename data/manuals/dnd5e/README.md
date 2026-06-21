# D&D 5ª edición — manuales locales

Coloca aquí tus PDFs de reglas. Por defecto **no se commitean** (repo público + copyright). Para tenerlos al programar desde el móvil y que Cursor AI los vea en el workspace, sigue **`docs/MANUALS_MOBILE.md`**.

## Core recomendado (MVP)

| Archivo sugerido | Contenido |
|---|---|
| `manual-del-jugador.pdf` | Player's Handbook / Manual del Jugador |
| `guia-dungeon-master.pdf` | Dungeon Master's Guide / Guía del DM |
| `manual-de-monstruos.pdf` | Monster Manual (opcional para combate/NPCs) |

Los nombres con prefijo `01D&D 5E - ...` también valen; el script de verificación los reconoce.

## Comprobar que los PDF están presentes

```powershell
cd C:\Users\lebre\Projects\role_pbp   # o la ruta de tu clone
.\scripts\verify-manuals.ps1
```

## Desarrollo desde el móvil

1. **Repo privado + Git LFS** (un solo clone): ver pasos en `docs/MANUALS_MOBILE.md` → Opción A. Tras clonar: `git lfs install` y `git lfs pull`.
2. **Repo público**: clona el código con git y sincroniza esta carpeta con OneDrive (u otro) desde el PC — Opción B en `docs/MANUALS_MOBILE.md`.

Abre la raíz del proyecto en Cursor en el móvil; los PDF deben estar en `data/manuals/dnd5e/` para que el agente pueda usarlos al importar o indexar.

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
