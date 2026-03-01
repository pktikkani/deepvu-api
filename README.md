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

### Setup

```bash
# Clone and install
git clone https://github.com/pktikkani/deepvu-api.git
cd deepvu-api
uv sync --all-extras

# Start infrastructure
docker compose up -d

# Copy env and configure
cp .env.example .env

# Run migrations (requires Postgres running)
uv run alembic upgrade head

# Start the server
uv run uvicorn deepvu.main:app --reload
```

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
