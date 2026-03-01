# DeepVu API

Multi-Tenant Ad Analytics Platform API — a white-labeled dashboard backend that replaces Apache Superset, providing complete data isolation via Row Level Security (RLS).

## Features

- **Multi-tenant architecture** with per-tenant branding, SSO config, and user management
- **Row Level Security** via SQL AST injection (sqlglot) — every analytics query is automatically filtered by `advertiser_id`
- **Two dashboard types**: Comprehensive (6 tabs) and Limited (3 tabs), assigned per tenant
- **RS256 JWT authentication** with single-use refresh token rotation
- **Rate limiting** (per-user and per-tenant) via Redis sliding window
- **CSS sanitization** for white-label custom styles
- **DuckDB analytics backend** (swappable to BigQuery)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Metadata DB | PostgreSQL 16 (async via asyncpg) |
| Analytics DB | DuckDB (BigQuery stub ready) |
| Cache | Redis 7 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | PyJWT (RS256) |
| SQL Parsing | sqlglot |
| Validation | Pydantic v2 |

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker & Docker Compose
- Redis 7 (running locally or via Docker)

### Setup

```bash
# Clone and install
git clone https://github.com/pktikkani/deepvu-api.git
cd deepvu-api
uv sync --all-extras

# Copy env and configure
cp .env.example .env
```

### Infrastructure

The project uses Docker for PostgreSQL and expects Redis to be running locally.

```bash
# Start PostgreSQL (mapped to port 5433 to avoid conflicts with local Postgres)
docker compose up -d postgres

# If you don't have Redis running locally, start it via Docker:
docker compose up -d redis
```

> **Note:** Docker Postgres is mapped to port **5433** (not 5432) to avoid conflicts with any local PostgreSQL installation. If you don't have a local Postgres, you can change the port back to `5432` in both `docker-compose.yml` and `.env`.

### Generate JWT Keys

The API uses RS256 JWT tokens. Generate a key pair before running:

```bash
mkdir -p keys
openssl genpkey -algorithm RSA -out keys/private.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -pubout -in keys/private.pem -out keys/public.pem
```

The `.env` file references these via `JWT_PRIVATE_KEY_PATH` and `JWT_PUBLIC_KEY_PATH`. You can also set `JWT_PRIVATE_KEY` and `JWT_PUBLIC_KEY` directly with the PEM content.

### Database Migrations

```bash
# Generate migration (only needed if models change)
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head
```

### Run the API

```bash
uv run uvicorn deepvu.main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://deepvu:deepvu_dev@localhost:5433/deepvu` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `JWT_PRIVATE_KEY_PATH` | `keys/private.pem` | Path to RSA private key |
| `JWT_PUBLIC_KEY_PATH` | `keys/public.pem` | Path to RSA public key |
| `JWT_ALGORITHM` | `RS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `RATE_LIMIT_PER_USER` | `100` | Requests per minute per user |
| `RATE_LIMIT_PER_TENANT` | `1000` | Requests per minute per tenant |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
| `GOOGLE_CLIENT_ID` | | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | | Google OAuth client secret |

### Run Tests

```bash
# Unit tests (no infrastructure needed)
uv run pytest tests/unit/ -v

# E2E multi-tenant isolation tests
uv run pytest tests/e2e/ -v

# Full suite with coverage
uv run pytest tests/ --cov=src/deepvu --cov-report=term
```

## API Endpoints

All endpoints are under `/api/v1/`:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/google/callback` | Public | Google OAuth callback |
| POST | `/auth/sso/callback` | Public | SSO callback |
| POST | `/auth/refresh` | Public | Rotate refresh token |
| GET | `/whitelabel/config` | Tenant | Get branding config |
| PUT | `/whitelabel/config` | Admin | Update branding |
| GET | `/users` | Admin | List tenant users |
| POST | `/users` | Admin | Create user |
| PATCH | `/users/{id}` | Admin | Update user |
| GET | `/dashboards` | Auth | Get dashboard config (tabs, filters, charts, tables) |
| POST | `/query` | Auth | Execute analytics query (RLS enforced, cached 15min) |
| POST | `/tenants` | Platform Admin | Create tenant |
| GET | `/tenants` | Platform Admin | List tenants |

## Dashboard Types

### Comprehensive (6 tabs)
- **Campaign Overview** — sub-tabs: Overall, YouTube
- **Reach & Frequency** — filters: Sub Campaign, Plan Line Item
- **Device Type** — 4 pie charts + Snapshot table (8 sortable columns)
- **Geo Trends** — sub-tabs: Region, City (pie chart + table side-by-side)
- **Placements**
- **Creative** — 5 filters + Creative Performance table (9 sortable columns)

### Limited (3 tabs)
- Campaign Overview, Geo Trends, Placements

## Project Structure

```
src/deepvu/
├── main.py              # App factory, middleware + router registration
├── config.py            # Pydantic Settings
├── dependencies.py      # FastAPI Depends (auth, tenant, analytics)
├── dashboard_config.py  # Tab definitions with UI structure
├── models/              # SQLAlchemy ORM (6 tables)
├── schemas/             # Pydantic request/response models
├── repositories/        # Data access layer
├── services/            # Business logic (CSS sanitizer)
├── analytics/           # Query abstraction (DuckDB + RLS injection)
├── middleware/           # Tenant resolver, rate limiter, auth, RLS, audit
└── routers/             # API endpoints
```

## Architecture

```
Request → CORS → Tenant Resolver → Rate Limiter → Auth → RLS → Audit Log → Router
                      ↓                                    ↓
                  Redis cache                        advertiser_id
                  (domain→tenant)                    injected into SQL
```

## License

Private — All rights reserved.
