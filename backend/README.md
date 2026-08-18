# Parasite SEO AI Automation — backend

Python FastAPI service for Phase 2A. This layer owns PostgreSQL, Redis, and the domain schema. It does **not** call OpenRouter, SEO/SERP APIs, or publishing platforms.

The Next.js app in the repository root remains the Phase 1 frontend and still uses mock data.

## Architecture

```
backend/
  app/
    main.py            FastAPI factory, CORS, lifespan
    core/              config, logging, security, errors
    db/                engine, sessions, seed
    models/            SQLAlchemy 2 mappings
    schemas/           Pydantic models
    repositories/      persistence helpers
    services/          redis + health
    api/               HTTP routes (health only in 2A)
    agents/            reserved for Phase 2B
    integrations/      reserved for later phases
    workers/           reserved for job queue
  alembic/             migrations
  tests/
```

Foreign keys use `RESTRICT` (or `SET NULL` for historical rows such as AI runs) so deleting a user, project, or content asset cannot silently wipe audit history.

## Phase 2B API layer

Base path: `/api/v1`

Envelope:

- success item: `{ "success": true, "data": {} }`
- success list: `{ "success": true, "data": [], "pagination": { "page", "page_size", "total" } }`
- error: `{ "success": false, "error": { "code", "message" } }`

Auth is prepared via `CurrentUser` / `X-User-Id`. Without a header, the seeded development user is used. JWT arrives in Phase 3.

Interactive docs: `http://127.0.0.1:8000/docs` and `/openapi.json`.

## Environment variables

Copy `.env.example` to `.env` and set real values. Required:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy URL, e.g. `postgresql+psycopg://user:pass@localhost:5434/parasite_seo` |
| `REDIS_URL` | e.g. `redis://localhost:6380/0` |
| `JWT_SECRET` | Signing key (min 16 characters). Unused by HTTP routes in 2A. |
| `JWT_ALGORITHM` | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL |
| `CORS_ORIGINS` | Comma-separated browser origins |
| `ENVIRONMENT` | `development`, `test`, or `production` |

Placeholders (not used in 2A): `OPENROUTER_API_KEY`, `AWS_*`, `SEO_PROVIDER_API_KEY`.

Never commit `.env`.

## Local setup (without Docker for the API)

1. Start Postgres and Redis (Docker Compose is the supported path):

   ```bash
   docker compose up -d postgres redis
   ```

2. Create a virtualenv and install dependencies:

   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```

3. Run migrations:

   ```bash
   alembic upgrade head
   ```

4. Optional development seed (refuses to run when `ENVIRONMENT=production`):

   ```bash
   python -m app.db.seed
   ```

5. Start the API:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

Health:

- `GET /health` — app + database + Redis
- `GET /health/db`
- `GET /health/redis`
- `GET /health/live`

## Docker

From the repository root:

```bash
docker compose up --build
```

Host ports default to **5434** (Postgres) and **6380** (Redis) so they do not collide with other local stacks. Inside the Compose network the backend still talks to `postgres:5432` and `redis:6379`.

Useful commands:

```bash
docker compose up -d postgres redis
docker compose logs -f backend
docker compose down
```

## Migrations

```bash
cd backend
alembic upgrade head
alembic downgrade -1
alembic revision -m "describe change"
```

All SQLAlchemy models are imported in `app.models` and registered with Alembic through `alembic/env.py` (`target_metadata = Base.metadata`).

## Tests

Postgres and Redis must be running and migrated.

```bash
cd backend
alembic upgrade head
pytest
```

## Redis

`app.services.redis` wraps connection, `ping`, and shutdown. There is no job queue in this phase.

## Next step (Phase 2B)

Do not start 2B from this README automatically. Phase 2B should add authenticated CRUD APIs that replace frontend mock data, still without the AI engine.
