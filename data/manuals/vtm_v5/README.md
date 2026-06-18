# Vampiro: La Mascarada V5 — manuales locales

Coloca aquí tus PDFs de reglas. **No se commitean** al repositorio.

## Core recomendado (MVP)

| Archivo sugerido | Contenido |
|---|---|
| `corebook.pdf` | Libro básico V5 |
| `chronicle-tenets.pdf` | Notas de crónica / opcional |

## Copiar manualmente

```powershell
# Ejemplo — ajusta la ruta de origen
Copy-Item "C:\ruta\a\tus\descargas\V5-Corebook.pdf" ".\corebook.pdf"
```

Tras copiar: `python backend/scripts/index_system_manuals.py --system vtm_v5`
