# CrimeGPT Deployment Guide

## 1. Development

### Quick start (Docker)

```bash
cp .env.example .env        # fill in JWT_SECRET, optional API keys
docker compose up -d
```

Services: PostgreSQL (5432), Redis (6379), backend (8000, uvicorn --reload),
translation (8001), Celery worker, frontend dev server (5173).

- Frontend: http://localhost:5173
- Swagger UI: http://localhost:8000/docs

### Zero-Docker mode

The backend runs standalone against SQLite (the default `DATABASE_URL`
is `sqlite+aiosqlite:///./crimegpt.db`):

```bash
cd backend
pip install -r requirements.txt        # core only; requirements-full.txt for AI extras
uvicorn app.main:app --reload
```

### Migrations

- **Development:** `init_db()` runs `Base.metadata.create_all` at startup —
  tables are created automatically, no migration step needed.
- **Production:** use Alembic against PostgreSQL:

```bash
docker compose exec backend alembic upgrade head
```

### Seeding demo data

```bash
docker compose exec backend python -m app.seeds.demo_data
# Seeded users: IO001 / SHO001 / LA001, password demo123
```

### Indexing the legal corpus (optional, needs chromadb)

```bash
docker compose exec backend python -m app.rag.indexer
```

If ChromaDB is not installed the RAG layer falls back to keyword search over
`backend/data/legal/*.json` — no indexing step required.

## 2. Production

Production uses `docker-compose.prod.yml` + nginx as reverse proxy and static
file server. The frontend is built once by a one-shot `frontend-build`
container into the shared `frontend_dist` volume, which nginx serves.

```bash
cp .env.example .env      # set strong JWT_SECRET, DB_PASSWORD, ENVIRONMENT=production
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml exec backend python -m app.seeds.demo_data   # optional
```

- nginx listens on 80 (and 443 once certificates are installed).
- The database is not exposed on the host in production.
- The backend runs uvicorn without `--reload`; Celery runs with concurrency 4.

### HTTPS with certbot (Let's Encrypt)

1. Point your domain's A record at the server.
2. Obtain certificates on the host:

```bash
sudo certbot certonly --standalone -d crimegpt.example.com
```

3. Uncomment the certificate mounts in `docker-compose.prod.yml` (nginx
   service) and the 443 `server` block in `nginx/nginx.conf`, replacing
   `crimegpt.example.com` with your domain.
4. Reload: `docker compose -f docker-compose.prod.yml restart nginx`.
5. Renewal: `certbot renew` via cron, then restart nginx.

## 3. Environment Variable Reference

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./crimegpt.db` | SQLAlchemy async URL. Use `postgresql+asyncpg://crimegpt:<pw>@db:5432/crimegpt` in Docker/prod. |
| `DB_PASSWORD` | — | PostgreSQL password (used by compose files). |
| `JWT_SECRET` | — | JWT signing key, min 32 chars. Must be changed in prod. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime. |
| `OPENAI_API_KEY` | empty | Optional; embeddings + summarization. Local embeddings used if unset. |
| `TRANSLATION_SERVICE_URL` | `http://localhost:8001` | IndicTrans2 microservice URL. |
| `GOOGLE_TRANSLATE_API_KEY` | empty | Optional translation fallback. |
| `UPLOAD_DIR` | `./uploads` | Generated documents and evidence files. |
| `CHROMA_DB_PATH` | `./chroma_db` | Persistent vector store path. |
| `REDIS_URL` | `redis://localhost:6379` | Redis for Celery/caching. |
| `USE_CELERY` | `false` | `true` = async document generation via Celery. |
| `GOOGLE_VISION_API_KEY` | empty | Optional OCR fallback. |
| `ENVIRONMENT` | `development` | `development` or `production`. |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated CORS origins. |

## 4. Backups

### PostgreSQL

```bash
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U crimegpt crimegpt | gzip > backup_$(date +%F).sql.gz
```

Restore: `gunzip -c backup.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U crimegpt crimegpt`

### ChromaDB and uploads

The vector store and generated documents are plain directories/volumes; back
them up with the database on the same schedule:

```bash
tar czf chroma_backup_$(date +%F).tgz chroma_db/
tar czf uploads_backup_$(date +%F).tgz uploads/
```

The ChromaDB index can always be rebuilt from `backend/data/` with
`python -m app.rag.indexer`, so the corpus JSON files (in git) are the source
of truth. Uploads and the database cannot be regenerated — back them up daily.
