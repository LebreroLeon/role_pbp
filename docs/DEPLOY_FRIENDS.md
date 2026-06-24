# Desplegar RolePBP para amigos (Neon + Render + Vercel)

Guía paso a paso para tener la app **pública 24/7** con tier gratuito. Ideal para PBP async: los amigos entran cuando pueden.

**Arquitectura:**

| Pieza | Servicio | URL ejemplo |
|---|---|---|
| Base de datos | [Neon](https://neon.tech) (PostgreSQL + pgvector) | interno |
| API + WebSockets | [Render](https://render.com) Web Service (Docker) | `https://rolepbp-api.onrender.com` |
| Frontend PWA | [Vercel](https://vercel.com) | `https://rolepbp.vercel.app` |

---

## Antes de empezar

- Cuenta GitHub con el repo `role_pbp` subido.
- Clave **OpenAI** (embeddings, Shadow Master, resúmenes). Sin ella: RAG y IA en fallback limitado.
- PDFs de manuales en `data/manuals/dnd5e/` (no se suben a Render; en **Docker local** se indexan solos al arrancar si `SEED_MANUALS=true`).
- **15–30 min** la primera vez.

---

## Paso 1 — Neon (PostgreSQL + pgvector)

1. Entra en [console.neon.tech](https://console.neon.tech) → **New Project**.
2. Nombre: `rolepbp`. Región: la más cercana a tus amigos (ej. `Frankfurt`).
3. En **Dashboard** → tu base de datos → **Connection string** → copia la URI **pooled** (recomendada para serverless/Render).
4. Convierte el prefijo para asyncpg (Neon suele incluir `?sslmode=require`; el backend lo traduce a SSL de asyncpg):
   - Neon te da: `postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`
   - Tú necesitas: `postgresql+asyncpg://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`
   - **No quites** `sslmode=require`: asyncpg no lo entiende en la URL, pero la app lo elimina y pasa `ssl=True` al conectar.
5. En Neon **SQL Editor**, ejecuta una vez:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

6. Guarda la URI convertida; la usarás en Render.

> **Tip:** Ejecuta `scripts/setup_neon.ps1` para ver estos pasos y comprobar la conexión desde tu PC.

---

## Paso 2 — Render (backend API)

### Opción A — Blueprint (`render.yaml` en el repo)

1. [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**.
2. Conecta el repo GitHub `role_pbp`.
3. Render detecta `render.yaml` y crea el servicio `rolepbp-api`.
4. Rellena las variables marcadas como **sync: false** (ver tabla abajo).

### Opción B — Web Service manual

1. **New** → **Web Service** → repo `role_pbp`.
2. Configuración:

| Campo | Valor |
|---|---|
| Root Directory | *(vacío — raíz del repo)* |
| Runtime | **Docker** |
| Dockerfile Path | `backend/Dockerfile` |
| Docker Context | `backend` |
| Plan | **Free** |
| Health Check Path | `/api/v1/health` |

3. **Start Command** (solo si NO usas Docker; runtime Python):

```bash
cd backend && pip install -r requirements.txt && python -m app.core.migrate && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Con Docker (recomendado) el `CMD` del Dockerfile ya hace migrate + uvicorn en `$PORT`.

### Variables de entorno en Render

| Variable | Valor | Obligatorio |
|---|---|---|
| `APP_ENV` | `production` | sí |
| `APP_DEBUG` | `false` | sí |
| `DATABASE_URL` | `postgresql+asyncpg://USER:PASS@ep-xxx.neon.tech/neondb?sslmode=require` (URI pooled de Neon, prefijo `+asyncpg`) | sí |
| `JWT_SECRET` | string aleatorio largo (`openssl rand -hex 32`) | sí |
| `OPENAI_API_KEY` | `sk-...` | sí (para IA/RAG) |
| `CORS_ORIGINS` | `https://TU-APP.vercel.app` (sin barra final) | sí |
| `UPLOAD_DIR` | `/tmp/campaign_uploads` (solo usado si `STORAGE_BACKEND=local`) | sí en local |
| `STORAGE_BACKEND` | `r2` en producción; `local` en desarrollo | sí |
| `R2_ACCOUNT_ID` | ID de cuenta Cloudflare (Dashboard → R2 → Overview) | sí con `r2` |
| `R2_ACCESS_KEY_ID` | Access Key del token S3 API de R2 | sí con `r2` |
| `R2_SECRET_ACCESS_KEY` | Secret Key del token (solo visible al crear el token) | sí con `r2` |
| `R2_BUCKET_NAME` | `rolepbp` | sí con `r2` |
| `SYSTEM_MANUALS_DIR` | `/tmp/manuals` | sí |
| `SEED_MANUALS` | `false` (por defecto; no indexa en Render sin PDFs en la imagen) | opcional |
| `SEED_MONSTERS` | `true` en Render (catálogo SRD ~325 criaturas en la imagen; upsert idempotente tras migraciones) | recomendado en producción |
| `SEED_MANUALS_SYSTEMS` | `dnd5e` o `dnd5e,vtm_v5` (vacío = todos los sistemas conocidos) | opcional |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | opcional |
| `EMBEDDING_DIMENSIONS` | `1536` | opcional |
| `LLM_MODEL` | `gpt-4o-mini` | opcional |

5. Deploy. Cuando termine, anota la URL: `https://rolepbp-api.onrender.com`.
6. Comprueba: `https://rolepbp-api.onrender.com/api/v1/health` → `{"status":"ok",...}`.

### Cloudflare R2 (almacenamiento persistente)

Los avatares, ilustraciones y documentos de campaña se guardan en R2 cuando `STORAGE_BACKEND=r2` (recomendado en Render). El bucket es privado: el frontend sigue usando las rutas `/api/v1/entities/{id}/avatar` y el backend hace de proxy con autenticación JWT.

1. En [Cloudflare Dashboard](https://dash.cloudflare.com) → **R2** → crea el bucket `rolepbp` (si no existe).
2. En **R2** → **Manage R2 API Tokens** → **Create API token**.
3. Permisos: **Object Read & Write** sobre el bucket `rolepbp`.
4. Copia **Access Key ID** y **Secret Access Key** al crear el token. El secret **solo se muestra una vez**; si lo pierdes, crea un token nuevo.
5. Anota tu **Account ID** (R2 → Overview, o en la URL del dashboard).
6. En Render, configura:

| Variable | Valor |
|---|---|
| `STORAGE_BACKEND` | `r2` |
| `R2_ACCOUNT_ID` | tu Account ID |
| `R2_ACCESS_KEY_ID` | Access Key del token |
| `R2_SECRET_ACCESS_KEY` | Secret Key del token |
| `R2_BUCKET_NAME` | `rolepbp` |

Estructura de claves en el bucket:

```
{campaign_id}/avatars/{entity_id}.{ext}
{campaign_id}/illustrations/{entity_id}.{ext}
{campaign_id}/documents/{document_id}.{ext}
```

En desarrollo local deja `STORAGE_BACKEND=local` y `UPLOAD_DIR=./campaign_uploads` (sin credenciales R2).

### Caveats Render Free

- **Duerme** tras ~15 min sin tráfico. El primer request tarda **~50 s** en despertar.
- Disco **efímero** en Render Free: con `STORAGE_BACKEND=r2` los uploads de campaña persisten en Cloudflare. Sin R2, avatares y PDFs subidos **se pierden** al redeploy/restart.
- WebSockets funcionan en Render; la primera conexión tras dormir también sufre el cold start.

---

## Paso 3 — Vercel (frontend PWA)

1. [vercel.com](https://vercel.com) → **Add New Project** → importa `role_pbp`.
2. Configuración:

| Campo | Valor |
|---|---|
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm install` |

3. **Environment Variables** (entorno Production):

| Variable | Valor |
|---|---|
| `VITE_API_URL` | `https://rolepbp-api.onrender.com` (tu URL Render, **sin** barra final) |

> **Importante:** `VITE_API_URL` se embebe en el JS en **build time**. Si la añades después del primer deploy, debes hacer **Redeploy** en Vercel. Sin ella, login/registro fallan con `Request failed: 405` (ver sección de troubleshooting al final).

4. Deploy. Anota la URL: `https://rolepbp-xxx.vercel.app`.

5. El archivo `frontend/vercel.json` reescribe rutas SPA (`/campaigns/...` → `index.html`) y **proxifica** `/api/*` a Render como red de seguridad si un build antiguo no tenía `VITE_API_URL`.

6. Vuelve a **Render** y actualiza `CORS_ORIGINS` con la URL real de Vercel. Redeploy backend si cambiaste CORS.

---

## Paso 4 — CORS (checklist)

`CORS_ORIGINS` en Render debe incluir **exactamente** el origen del SPA:

```
https://rolepbp-xxx.vercel.app
```

- Protocolo `https://` obligatorio.
- Sin path (`/`) ni barra final.
- Si añades dominio custom en Vercel, añádelo separado por coma:
  `https://rolepbp.vercel.app,https://partida.tudominio.com`

---

## Paso 5 — Manuales del sistema (RAG)

### Docker local (desarrollo)

Con `docker compose up`, el backend arranca con `SEED_MANUALS=true`: tras las migraciones Alembic, indexa automáticamente los PDFs montados en `data/manuals/{system_id}/` **solo la primera vez** (si la BD no tiene chunks para ese sistema). Necesitas `OPENAI_API_KEY` en `.env` y los PDFs en disco.

- Reindexar todo: `SEED_MANUALS=force` en `docker-compose.yml` (un arranque) o el script manual abajo.
- Solo D&D: `SEED_MANUALS_SYSTEMS=dnd5e`.

### Render / Neon (producción)

Los PDFs **no van en la imagen Docker de Render** (`/tmp/manuals` está vacío). `SEED_MANUALS=true` en Render **no sirve** sin copiar PDFs al servidor — el arranque lo detecta y continúa sin error.

Indexa **una vez desde tu PC** apuntando a Neon (los chunks persisten en la BD; no hace falta repetir en cada deploy):

1. Copia PDFs a `data/manuals/dnd5e/` (ver `data/manuals/dnd5e/README.md`).
2. En la raíz del repo, crea/edita `.env` (o exporta variables):

```env
DATABASE_URL=postgresql+asyncpg://USER:PASS@ep-xxx.neon.tech/neondb?sslmode=require
OPENAI_API_KEY=sk-...
SYSTEM_MANUALS_DIR=./data/manuals
```

3. Desde `backend/`:

```powershell
cd backend
python scripts/index_system_manuals.py --system dnd5e
```

4. Repite `--system cyberpunk_red` o `--system vtm_v5` si los usáis.
5. Verifica en la app (logueado como máster): consulta de reglas / Shadow Master modo reglas.

> Los chunks quedan en Neon; no hace falta repetir en cada deploy de Render.

---

## Paso 6 — Invitar amigos

### Registro

1. Comparte la URL de Vercel: `https://rolepbp-xxx.vercel.app`
2. Cada amigo: **Registrarse** con email + contraseña + nombre visible.
3. No hay email de verificación aún; el email es solo identificador de cuenta.

### Añadir a la campaña

1. Tú (máster) creas la campaña en la app.
2. En **Hub de campaña** o **Mesa del máster** → **Invitar jugador**.
3. Introduce el **email exacto** con el que se registró el amigo.
4. El amigo verá la campaña en su lista al iniciar sesión.

### Email de campaña (manual)

Envía un correo/WhatsApp con:

```
¡Partida PBP RolePBP!

1. Regístrate: https://rolepbp-xxx.vercel.app
2. Usa este email: [su email]
3. Cuando esté hecho, avísame y te añado a "Nombre de la campaña"

Nota: la primera carga puede tardar ~1 min (servidor gratis).
```

---

## Paso 7 — PWA en móvil

### Android (Chrome)

1. Abre la URL de Vercel en Chrome.
2. Menú (⋮) → **Instalar aplicación** o **Añadir a pantalla de inicio**.
3. Icono "RolePBP" en el launcher; abre en pantalla completa.

### iOS (Safari)

1. Abre la URL en Safari.
2. Compartir → **Añadir a pantalla de inicio**.
3. Safari no muestra banner de instalación automático; hay que hacerlo manual.

La PWA usa `vite-plugin-pwa` con `display: standalone`. Las actualizaciones del frontend se aplican al recargar (autoUpdate).

---

## Paso 8 — Probar el flujo completo

- [ ] Health: `GET /api/v1/health` en Render
- [ ] Registro + login en Vercel
- [ ] Crear campaña, invitar amigo por email
- [ ] Amigo ve la campaña y puede postear en escena
- [ ] Chat OOC y WebSocket (escena activa; puede tardar si Render dormía)
- [ ] Tirada de dados en escena
- [ ] Shadow Master (si `OPENAI_API_KEY` configurada)
- [ ] Instalar PWA en móvil

---

## Limitaciones conocidas

| Limitación | Detalle |
|---|---|
| **Sin push notifications** | Aún no implementadas. Los amigos deben entrar por su cuenta o por WhatsApp/email de campaña. |
| **Render duerme** | Free tier: cold start ~50 s. Aceptable para PBP async, no para tiempo real. |
| **Uploads efímeros** | Avatares y documentos en `/tmp` se pierden al reiniciar Render. |
| **Manuales** | Docker dev: auto con `SEED_MANUALS=true`. Render: indexación manual desde PC (PDFs no en la nube). |
| **OpenAI coste** | Embeddings + LLM consumen crédito según uso. |

---

## Comandos útiles

```powershell
# Build frontend (local)
cd frontend
npm run build

# Tests smoke backend
cd backend
pytest tests/test_deploy_smoke.py -q

# Reindexar manuales
cd backend
$env:DATABASE_URL="postgresql+asyncpg://..."
python scripts/index_system_manuals.py --system dnd5e --force
```

---

## Resumen de URLs y variables

```
Vercel  → VITE_API_URL=https://rolepbp-api.onrender.com
Render  → CORS_ORIGINS=https://rolepbp-xxx.vercel.app
Render  → DATABASE_URL=postgresql+asyncpg://...@neon...?sslmode=require
Render  → JWT_SECRET=<aleatorio>
Render  → OPENAI_API_KEY=sk-...
Health  → https://rolepbp-api.onrender.com/api/v1/health
```

Si algo falla: revisa logs en Render (Events / Logs) y Vercel (Deployments → Build Logs). Errores frecuentes:

### Login / registro: `Request failed: 405`

**Causa:** el frontend hace `POST /api/v1/auth/login` contra el **origen de Vercel** porque `VITE_API_URL` estaba vacío en el **build** (o el navegador sigue usando un **bundle antiguo** en caché / Service Worker). Sin proxy, `frontend/vercel.json` reescribe `/api/...` a `index.html` y un `POST` al HTML estático devuelve **405 Method Not Allowed**.

**Comprobar:** en DevTools → **Network** (Red), la petición de login debe ir a `https://rolepbp-api.onrender.com/api/v1/auth/login`, **no** a `https://role-pbp.vercel.app/api/v1/auth/login`.

**Arreglo (Vercel):**

1. [vercel.com](https://vercel.com) → tu proyecto → **Settings** (⚙️) → **Environment Variables**.
2. Añade o edita:
   - **Key:** `VITE_API_URL`
   - **Value:** `https://rolepbp-api.onrender.com` (sin barra final)
   - **Environments:** marca **Production** (y **Preview** si quieres). Si solo está en **Development**, el deploy de producción **no** la usa.
3. **Deployments** → el último deploy → menú **⋯** → **Redeploy** (obligatorio: Vite inyecta `VITE_*` en tiempo de build).
4. En el navegador: **recarga forzada** (`Ctrl+Shift+R` en Windows, `Cmd+Shift+R` en Mac) o abre **ventana de incógnito**. Si instalaste la PWA, cierra la app y borra datos del sitio, o en DevTools → **Application** → **Service Workers** → **Unregister**.
5. Vuelve a **Network** y confirma que la URL del login es `rolepbp-api.onrender.com`.

**Arreglo (Render — CORS):**

En Render → servicio `rolepbp-api` → **Environment** → `CORS_ORIGINS` debe ser **exactamente**:

```
https://role-pbp.vercel.app
```

(sin barra final, sin path). Si cambias CORS, **Manual Deploy** en Render.

Desde una versión reciente del repo, el build en Vercel **falla** si falta `VITE_API_URL`, para evitar desplegar un bundle roto. `vercel.json` también proxifica `/api/*` a Render como respaldo para bundles viejos en caché.

### Login / registro: no pasa nada (incógnito, sin mensaje de error)

**Causa:** el build ya llama a `https://rolepbp-api.onrender.com`, pero **CORS** en Render no incluye tu URL de Vercel. El navegador bloquea la petición antes de llegar al servidor (`Failed to fetch`); en versiones antiguas del frontend eso no se mostraba en pantalla.

**Comprobar (incógnito → F12 → Network):**

1. Al pulsar Entrar/Registrarse debe aparecer `OPTIONS` y luego `POST` a `rolepbp-api.onrender.com/api/v1/auth/login` (o `register`).
2. Si `OPTIONS` devuelve **400** con cuerpo `Disallowed CORS origin`, falta `CORS_ORIGINS`.
3. Si la petición va a `role-pbp.vercel.app/api/...` con **405**, el navegador usa un bundle viejo (Service Worker) — ver arriba.

**Arreglo (Render — obligatorio):**

En Render → servicio `rolepbp-api` → **Environment** → `CORS_ORIGINS`:

```
https://role-pbp.vercel.app
```

Manual Deploy en Render. Prueba de preflight (PowerShell / bash):

```bash
curl.exe -X OPTIONS "https://rolepbp-api.onrender.com/api/v1/auth/login" ^
  -H "Origin: https://role-pbp.vercel.app" ^
  -H "Access-Control-Request-Method: POST" ^
  -H "Access-Control-Request-Headers: content-type" -i
```

Debe responder **200 OK** con `access-control-allow-origin: https://role-pbp.vercel.app`.

### Otros errores frecuentes

- `CORS_ORIGINS` sin coincidir con la URL de Vercel.
- `TypeError: connect() got an unexpected keyword argument 'sslmode'` → despliega la versión actual del repo (el backend traduce `sslmode` para asyncpg) o usa la URI de Neon tal cual con `?sslmode=require` tras el deploy.
