# Manuales de sistema (local)

PDFs oficiales de reglas **no se suben al repositorio** (copyright). Coloca aquí tus copias locales por sistema de juego.

## Estructura

```
data/manuals/
├── dnd5e/          ← D&D 5ª edición
├── vtm_v5/         ← Vampiro: La Mascarada V5
└── cyberpunk_red/  ← Cyberpunk RED
```

## Cómo añadir manuales

1. Copia tus PDFs a la carpeta del `system_id` correspondiente (ver README en cada subcarpeta).
2. Usa nombres en ASCII kebab-case cuando puedas (`manual-del-jugador.pdf`).
3. Desde la raíz del repo, ejecuta el indexador (cuando esté implementado):

   ```bash
   cd backend
   python scripts/index_system_manuals.py --system dnd5e
   ```

4. Comprueba en la UI (Biblioteca / Mesa del Máster) que el estado sea «Indexado».

Diseño completo: `docs/07_system_manuals.md`.
