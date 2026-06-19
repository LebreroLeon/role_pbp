# Despliegue producción ($0 / hobby)

Guía mínima para desplegar RolePBP **sin crear cuentas por ti**. El repo incluye `docker-compose.prod.yml` para un stack autocontenido en un VPS o máquina propia.

## Requisitos

- Docker + Docker Compose v2
- Dominio o IP pública (opcional HTTPS con Caddy/Traefik fuera de este doc)
- Clave OpenAI (embeddings, Shadow Master, resúmenes)
- `JWT_SECRET` largo y aleatorio

## Variables

Copia `.env.production.example` → `.env` en la raíz del proyecto y rellena:

| Variable | Notas |
|---|---|
| `DATABASE_URL` | En compose prod usa el hostname `postgres` |
| `JWT_SECRET` | Obligatorio en prod |
| `OPENAI_API_KEY` | Sin ella: RAG y IA en fallback |
| `CORS_ORIGINS` | URL(s) del frontend, ej. `https://rolepbp.tudominio.com` |
| `VITE_API_URL` | Dejar vacío si nginx hace proxy `/api` → backend |

Volúmenes persistentes:

- `postgres_data` — base de datos
- `campaign_uploads` — avatares y documentos de biblioteca
- Montar `data/manuals` si indexas manuales de sistema

## Stack Docker (recomendado hobby)

```bash
# Desde la raíz del repo
cp .env.production.example .env
# Editar .env con tus secretos

docker compose -f docker-compose.prod.yml up -d --build
```

Servicios:

| Servicio | Puerto | Rol |
|---|---|---|
| `postgres` | 5432 (interno) | PostgreSQL + pgvector |
| `backend` | 8000 (interno) | FastAPI, migraciones Alembic al arrancar |
| `frontend` | 8080 | nginx sirviendo `frontend/dist`, proxy `/api` y WS |

Healthcheck: `GET http://localhost:8080/api/health` (vía proxy) o `GET http://backend:8000/health` dentro de la red Docker.

## Migraciones

El contenedor backend ejecuta `python -m app.core.migrate` antes de uvicorn (sin `--reload`).

Para reindexar manuales tras el primer deploy:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python scripts/index_system_manuals.py --system dnd5e
```

## Alternativas gratuitas (manual)

| Pieza | Opción $0 |
|---|---|
| Frontend estático | Vercel / Cloudflare Pages — build `cd frontend && npm run build`, `VITE_API_URL=https://api.tudominio.com` |
| API | Railway / Render free tier / Fly.io |
| Postgres | Railway Postgres, Neon free (caduca a 90 d en Render), o Postgres en el mismo VPS |

No desplegamos estos servicios desde el repo; solo documentamos el patrón.

## Checklist pre-lanzamiento

- [ ] `JWT_SECRET` distinto del ejemplo
- [ ] `APP_DEBUG=false`
- [ ] CORS apunta al host real del SPA
- [ ] Volumen persistente para `campaign_uploads`
- [ ] Backup de `postgres_data`
- [ ] Probar registro, crear campaña, subir documento, Shadow Master modo campaña

## Desarrollo vs producción

| | Dev (`docker-compose.yml`) | Prod (`docker-compose.prod.yml`) |
|---|---|---|
| Backend | `--reload`, código montado | Sin reload, imagen fija |
| Frontend | Vite dev server :5173 | nginx + build estático :8080 |
| Hot reload | Sí | No |
