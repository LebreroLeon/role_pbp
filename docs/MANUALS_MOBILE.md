# Manuales en móvil y acceso para Cursor AI

Los PDF de reglas (~1,1 GB en `data/manuals/dnd5e/`) **no están en GitHub** mientras el repositorio sea **público** (contenido con copyright). En el PC local siguen en la carpeta del proyecto; Cursor y los scripts de importación los leen desde ahí.

## Visibilidad del repo

| Estado | PDFs en GitHub | Recomendación |
|--------|----------------|---------------|
| **Público** (actual) | No | Sincronizar manuales aparte (OneDrive) o hacer el repo privado antes de Git LFS |
| **Privado** | Sí, vía Git LFS | Mejor opción para clonar en el móvil con un solo `git lfs pull` |

Comprobar visibilidad:

```powershell
gh auth login   # una vez
gh repo view LebreroLeon/role_pbp --json visibility,isPrivate
```

Hacer el repo privado (solo si eres el dueño y aceptas perder visibilidad pública):

```powershell
gh repo edit LebreroLeon/role_pbp --visibility private
```

## Opción A — Repo privado + Git LFS (recomendada para móvil + IA)

Tras hacer el repo **privado**, en el PC donde ya tienes los PDF:

```powershell
cd C:\Users\lebre\Projects\role_pbp
git lfs install
git lfs track "data/manuals/**/*.pdf"
git add .gitattributes
```

En `.gitignore`, **elimina o comenta** estas líneas:

```
data/manuals/**/*.pdf
data/manuals/**/*.PDF
```

Luego:

```powershell
git add data/manuals/dnd5e/*.pdf
git commit --trailer "Co-authored-by: Cursor <cursoragent@cursor.com>" -m "Track D&D manuals with Git LFS for private dev clones"
git push origin main
```

En el móvil (o cualquier clone nuevo):

```powershell
git clone https://github.com/LebreroLeon/role_pbp.git
cd role_pbp
git lfs install
git lfs pull
.\scripts\verify-manuals.ps1
```

Abre esa carpeta en Cursor (móvil o escritorio): los PDF quedan en el workspace y el agente puede leerlos para importación y desarrollo.

**Notas LFS:** GitHub incluye ~1 GB de almacenamiento LFS en plan gratuito; ~1,1 GB puede requerir un pack pequeño de datos LFS. Los punteros LFS van en git; los binarios en el almacén LFS.

## Opción B — Repo público + sincronización local (sin subir PDFs)

Mantén el `.gitignore` actual. Sincroniza la carpeta del proyecto (o solo `data/manuals/dnd5e`) con **OneDrive**, **Syncthing**, etc.

1. En el PC: el proyecto vive bajo una ruta sincronizada, p. ej. `OneDrive\Projects\role_pbp`.
2. En el móvil: espera a que OneDrive termine de bajar `data/manuals/dnd5e\*.pdf`.
3. Clona o abre el repo en esa misma ruta sincronizada (git para código; PDFs llegan por la nube de archivos, no por `git pull`).

Verificación:

```powershell
.\scripts\verify-manuals.ps1
```

## Opción C — Submodule privado (repo público + PDFs en repo privado aparte)

Si quieres **código público** pero manuales solo en un repo privado:

1. Crea `LebreroLeon/role_pbp-manuals` (privado), sube PDFs con LFS.
2. En `role_pbp`: `git submodule add <url-privado> data/manuals/dnd5e`
3. En el móvil: `git clone --recurse-submodules` y `git lfs pull` dentro del submodule.

Requiere acceso GitHub en el dispositivo móvil al repo privado del submodule.

## Cursor AI

- Los PDF deben existir **en disco dentro del workspace** abierto en Cursor (`data/manuals/dnd5e/`).
- Tras importar monstruos/reglas a la base de datos, el runtime puede no necesitar los PDF; siguen siendo útiles para desarrollo e indexación (`index_system_manuals.py`).

## Referencia

- Lista de archivos y copia desde Descargas: `data/manuals/dnd5e/README.md`
