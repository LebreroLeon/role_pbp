# Cyberpunk RED — manuales locales

Coloca aquí tus PDFs de reglas. **No se commitean** al repositorio.

## Core recomendado (MVP)

| Archivo sugerido | Contenido |
|---|---|
| `core-rulebook.pdf` | Core Rulebook |
| `jumpstart.pdf` | Jumpstart Kit (opcional) |

## Copiar manualmente

```powershell
# Ejemplo — ajusta la ruta de origen
Copy-Item "C:\ruta\a\tus\descargas\Cyberpunk-RED-Core.pdf" ".\core-rulebook.pdf"
```

Tras copiar: `python backend/scripts/index_system_manuals.py --system cyberpunk_red`
