# DeepVu API — Architecture & API Reference

> **Purpose**: This document is the single source of truth for the frontend (React) team to understand the backend API, data models, authentication flow, and integration patterns. Everything needed to build the UI is here.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Authentication & Authorization](#2-authentication--authorization)
3. [Multi-Tenancy Model](#3-multi-tenancy-model)
4. [API Base URL & Common Headers](#4-api-base-url--common-headers)
5. [API Endpoints — Complete Reference](#5-api-endpoints--complete-reference)
6. [Dashboard Configuration API](#6-dashboard-configuration-api)
7. [Analytics Query API](#7-analytics-query-api)
8. [White-Label / Branding API](#8-white-label--branding-api)
9. [User Management API](#9-user-management-api)
10. [Tenant Management API](#10-tenant-management-api)
11. [Data Models & Database Schema](#11-data-models--database-schema)
12. [Error Handling](#12-error-handling)
13. [Rate Limiting](#13-rate-limiting)
14. [Middleware Pipeline](#14-middleware-pipeline)
15. [Dashboard Tab Definitions](#15-dashboard-tab-definitions)
16. [Frontend Integration Guide](#16-frontend-integration-guide)

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                         │
│  (White-labeled per tenant: logo, colors, custom CSS)       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│                                                             │
│  Middleware Pipeline (per request):                          │
│  ┌─────────┐ ┌──────────┐ ┌──────┐ ┌─────┐ ┌─────────┐    │
│  │  CORS   │→│ Tenant   │→│ Rate │→│Auth │→│  Audit  │    │
│  │         │ │ Resolver │ │Limit │ │ JWT │ │  Log    │    │
│  └─────────┘ └──────────┘ └──────┘ └─────┘ └─────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Routers    │  │  Services    │  │  Repositories    │  │
│  │  (6 groups)  │→ │  (business   │→ │  (data access)   │  │
│  │              │  │   logic)     │  │                  │  │
│  └──────────────┘  └──────────────┘  └────────┬─────────┘  │
│                                               │             │
│         ┌─────────────────────────────────────┤             │
│         ▼                                     ▼             │
│  ┌──────────────┐                   ┌──────────────────┐   │
│  │  PostgreSQL  │                   │     DuckDB       │   │
│  │  (metadata)  │                   │   (analytics)    │   │
│  │              │                   │ + RLS injection  │   │
│  └──────────────┘                   └──────────────────┘   │
│         ▲                                                   │
│         │                                                   │
│  ┌──────────────┐                                          │
│  │    Redis     │  (JWT refresh tokens, rate limits,       │
│  │              │   tenant domain cache, query cache)      │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Framework | FastAPI 0.115+ | Async REST API |
| Metadata DB | PostgreSQL 16 | Tenants, users, branding, RLS policies |
| Analytics DB | DuckDB (in-memory, seeded at startup) | Ad performance data (swappable to BigQuery) |
| Cache/Sessions | Redis 7 | Refresh tokens, rate limits, query cache, domain cache |
| ORM | SQLAlchemy 2.0 (async) | Database operations |
| Auth | PyJWT with RS256 | JSON Web Tokens |
| SQL Security | sqlglot | SQL AST parsing for RLS injection |
| Validation | Pydantic v2 | Request/response schemas |

---

## 2. Authentication & Authorization

### 2.1 JWT Access Tokens

All authenticated requests require an **RS256-signed JWT** access token.

**How to send the token** (two options):
```
Authorization: Bearer <access_token>
```
or as an `access_token` cookie.

**Token payload structure:**
```json
{
  "sub": "user-uuid",           // User ID
  "tenant_id": "tenant-uuid",   // Tenant the user belongs to
  "role": "viewer",             // One of: platform_admin, advertiser_admin, analyst, viewer
  "email": "user@example.com",
  "exp": 1709312400,            // Expires in 60 minutes
  "iat": 1709308800,
  "type": "access"
}
```

### 2.2 Refresh Token Flow

Refresh tokens are **single-use** (rotation). After using a refresh token, the old one is invalidated and a new pair (access + refresh) is returned.

```
POST /api/v1/auth/refresh
{
  "refresh_token": "uuid-string"
}

→ 200 OK
{
  "access_token": "eyJ...",
  "refresh_token": "new-uuid-string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

- Refresh tokens are stored in Redis with a **7-day TTL**
- Reusing an already-rotated refresh token returns `401`
- Access tokens expire in **60 minutes**

### 2.3 Role Hierarchy

| Role | Scope | Permissions |
|------|-------|------------|
| `platform_admin` | Global | Create/manage tenants, list all tenants |
| `advertiser_admin` | Per-tenant | Manage users, update branding, full data access |
| `analyst` | Per-tenant | View dashboards, run queries |
| `viewer` | Per-tenant | View dashboards only |

### 2.4 Auth Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/auth/google/callback` | POST | Public | Google OAuth callback (returns token pair) |
| `/api/v1/auth/sso/callback` | POST | Public | SSO provider callback |
| `/api/v1/auth/refresh` | POST | Public | Rotate refresh token |

---

## 3. Multi-Tenancy Model

Every request is scoped to a **tenant**. Tenants are isolated — users, branding, analytics data are completely separate.

### 3.1 Tenant Resolution

The backend resolves the tenant from the request in this priority order:

1. **Redis domain cache** — hostname → tenant_id (5-min TTL)
2. **Subdomain extraction** — `acme.deepvu.io` → slug `acme`
3. **`X-Tenant-ID` header** — explicit UUID

**For the frontend**: Always send the `X-Tenant-ID` header on authenticated requests:
```
X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000
```

### 3.2 Row Level Security (RLS)

Every analytics query is automatically wrapped with an `advertiser_id` filter using SQL AST manipulation (sqlglot). The frontend does **not** need to add tenant filters to queries — this is enforced server-side.

Example: if the frontend sends:
```sql
SELECT campaign, impressions FROM ad_metrics WHERE impressions > 1000
```

The backend transforms it to:
```sql
SELECT campaign, impressions FROM ad_metrics WHERE (impressions > 1000) AND advertiser_id = 'adv_tenant_123'
```

Security guarantees:
- `OR 1=1` bypass attempts are blocked (existing WHERE is parenthesized)
- Subquery wrapping is filtered
- UNION-based bypasses are filtered
- All DML (INSERT/UPDATE/DELETE) and DDL (CREATE/DROP/ALTER) are rejected

---

## 4. API Base URL & Common Headers

```
Base URL: https://<domain>/api/v1
```

### Required Headers

| Header | When | Example |
|--------|------|---------|
| `Authorization` | All authenticated endpoints | `Bearer eyJ...` |
| `X-Tenant-ID` | All tenant-scoped endpoints | `550e8400-e29b-41d4-a716-446655440000` |
| `Content-Type` | POST/PUT/PATCH requests | `application/json` |

### Common Response Headers

| Header | When | Meaning |
|--------|------|---------|
| `Retry-After` | 429 responses | Seconds to wait before retrying |

---

## 5. API Endpoints — Complete Reference

| Method | Path | Auth Required | Role | Description |
|--------|------|:---:|------|-------------|
| `POST` | `/auth/google/callback` | No | — | Google OAuth login |
| `POST` | `/auth/sso/callback` | No | — | SSO provider login |
| `POST` | `/auth/refresh` | No | — | Rotate refresh token |
| `GET` | `/whitelabel/config` | Tenant | Any | Get tenant branding |
| `PUT` | `/whitelabel/config` | Yes | `advertiser_admin` | Update branding |
| `GET` | `/users` | Yes | `platform_admin`, `advertiser_admin` | List users |
| `POST` | `/users` | Yes | `advertiser_admin` | Create user |
| `PATCH` | `/users/{user_id}` | Yes | `advertiser_admin` | Update user |
| `GET` | `/dashboards` | Yes | Any authenticated | Get dashboard config |
| `POST` | `/query` | Yes | Any authenticated | Execute analytics query |
| `POST` | `/tenants` | Yes | `platform_admin` | Create tenant |
| `GET` | `/tenants` | Yes | `platform_admin` | List all tenants |
| `GET` | `/tenants/{tenant_id}` | Yes | `platform_admin` | Get tenant details |
| `PATCH` | `/tenants/{tenant_id}` | Yes | `platform_admin` | Update tenant |
| `GET` | `/health` | No | — | Health check |

---

## 6. Dashboard Configuration API

### `GET /api/v1/dashboards`

Returns the full dashboard structure for the authenticated user's tenant. This is the **primary endpoint the frontend uses to render the dashboard layout**.

**Headers:** `Authorization: Bearer <token>`, `X-Tenant-ID: <uuid>`

**Response** (comprehensive type):
```json
{
  "dashboard_type": "comprehensive",
  "tabs": [
    {
      "key": "campaign_overview",
      "label": "Campaign Overview",
      "order": 1,
      "sub_tabs": [
        { "key": "overall", "label": "Overall", "charts": [], "tables": [] },
        { "key": "youtube", "label": "YouTube", "charts": [], "tables": [] }
      ],
      "filters": [],
      "charts": [],
      "tables": []
    },
    {
      "key": "reach_frequency",
      "label": "Reach & Frequency",
      "order": 2,
      "sub_tabs": [],
      "filters": [
        { "key": "sub_campaign", "label": "Sub Campaign", "type": "dropdown", "layout": null },
        { "key": "plan_line_item", "label": "Plan Line Item", "type": "dropdown", "layout": null }
      ],
      "charts": [],
      "tables": []
    },
    {
      "key": "device_type",
      "label": "Device Type",
      "order": 3,
      "sub_tabs": [],
      "filters": [
        { "key": "sub_campaign", "label": "Sub Campaign", "type": "dropdown", "layout": null },
        { "key": "plan_line_item", "label": "Plan Line Item", "type": "dropdown", "layout": null }
      ],
      "charts": [
        { "key": "device_type_spends", "label": "Device Type by Spends", "type": "pie" },
        { "key": "device_type_impressions", "label": "Device Type by Impressions", "type": "pie" },
        { "key": "device_type_clicks", "label": "Device Type by Clicks", "type": "pie" },
        { "key": "device_type_views", "label": "Device Type by Views", "type": "pie" }
      ],
      "tables": [
        {
          "key": "snapshot",
          "label": "Snapshot",
          "layout": null,
          "columns": [
            { "key": "device_type", "label": "Device Type", "sortable": true },
            { "key": "currency", "label": "Currency", "sortable": true },
            { "key": "spends", "label": "Spends", "sortable": true },
            { "key": "impressions", "label": "Impressions", "sortable": true },
            { "key": "clicks", "label": "Clicks", "sortable": true },
            { "key": "ctr", "label": "CTR", "sortable": true },
            { "key": "views", "label": "Views", "sortable": true },
            { "key": "vtr", "label": "VTR", "sortable": true }
          ]
        }
      ]
    },
    {
      "key": "geo_trends",
      "label": "Geo Trends",
      "order": 4,
      "sub_tabs": [
        {
          "key": "region",
          "label": "Region",
          "charts": [
            { "key": "spends_share", "label": "Spends Share", "type": "pie" }
          ],
          "tables": [
            {
              "key": "tabular_view",
              "label": "Tabular View",
              "layout": "side_by_side_with_chart",
              "columns": [
                { "key": "region", "label": "Region", "sortable": true },
                { "key": "currency", "label": "Currency", "sortable": true },
                { "key": "spends", "label": "Spends", "sortable": true },
                { "key": "impressions", "label": "Impressions", "sortable": true },
                { "key": "cpm", "label": "CPM", "sortable": true }
              ]
            }
          ]
        },
        {
          "key": "city",
          "label": "City",
          "charts": [
            { "key": "spends_share", "label": "Spends Share", "type": "pie" }
          ],
          "tables": [
            {
              "key": "tabular_view",
              "label": "Tabular View",
              "layout": "side_by_side_with_chart",
              "columns": [
                { "key": "city", "label": "City", "sortable": true },
                { "key": "currency", "label": "Currency", "sortable": true },
                { "key": "spends", "label": "Spends", "sortable": true },
                { "key": "impressions", "label": "Impressions", "sortable": true },
                { "key": "cpm", "label": "CPM", "sortable": true }
              ]
            }
          ]
        }
      ],
      "filters": [
        { "key": "sub_campaign", "label": "Sub Campaign", "type": "dropdown", "layout": "inline" },
        { "key": "plan_line_item", "label": "Plan Line Item", "type": "dropdown", "layout": "inline" }
      ],
      "charts": [],
      "tables": []
    },
    {
      "key": "placements",
      "label": "Placements",
      "order": 5,
      "sub_tabs": [],
      "filters": [],
      "charts": [],
      "tables": []
    },
    {
      "key": "creative",
      "label": "Creative",
      "order": 6,
      "sub_tabs": [],
      "filters": [
        { "key": "sub_campaign", "label": "Sub Campaign", "type": "dropdown", "layout": "inline" },
        { "key": "plan_line_item", "label": "Plan Line Item", "type": "dropdown", "layout": "inline" },
        { "key": "format", "label": "Format", "type": "dropdown", "layout": "inline" },
        { "key": "concept", "label": "Concept", "type": "dropdown", "layout": "inline" },
        { "key": "size", "label": "Size", "type": "dropdown", "layout": "inline" }
      ],
      "charts": [],
      "tables": [
        {
          "key": "creative_performance",
          "label": "Creative Performance",
          "layout": null,
          "columns": [
            { "key": "creative", "label": "Creative", "sortable": true },
            { "key": "creative_name", "label": "Creative Name", "sortable": true },
            { "key": "format", "label": "Format", "sortable": true },
            { "key": "currency", "label": "Currency", "sortable": true },
            { "key": "spends", "label": "Spends", "sortable": true },
            { "key": "impressions", "label": "Impressions", "sortable": true },
            { "key": "cpm", "label": "CPM", "sortable": true },
            { "key": "clicks", "label": "Clicks", "sortable": true },
            { "key": "ctr", "label": "CTR", "sortable": true }
          ]
        }
      ]
    }
  ]
}
```

**Response** (limited type — 3 tabs only):
```json
{
  "dashboard_type": "limited",
  "tabs": [
    { "key": "campaign_overview", "label": "Campaign Overview", "order": 1, "..." : "..." },
    { "key": "geo_trends", "label": "Geo Trends", "order": 2, "..." : "..." },
    { "key": "placements", "label": "Placements", "order": 3, "..." : "..." }
  ]
}
```

### Response Schema Reference

```typescript
// TypeScript types for the frontend

interface DashboardConfigResponse {
  dashboard_type: "comprehensive" | "limited";
  tabs: DashboardTab[];
}

interface DashboardTab {
  key: string;          // Unique identifier, e.g. "campaign_overview"
  label: string;        // Display label, e.g. "Campaign Overview"
  order: number;        // Tab order (1-based)
  sub_tabs: SubTab[];   // Nested tabs within this tab
  filters: FilterConfig[];  // Dropdown filters at the top of the tab
  charts: ChartConfig[];    // Charts to render
  tables: TableSchema[];    // Tables to render
}

interface SubTab {
  key: string;
  label: string;
  charts: ChartConfig[];
  tables: TableSchema[];
}

interface FilterConfig {
  key: string;          // Filter parameter name for API queries
  label: string;        // Display label
  type: "dropdown";     // Always "dropdown" for now
  layout: "inline" | null;  // "inline" = render side-by-side in a row
}

interface ChartConfig {
  key: string;          // Chart identifier
  label: string;        // Display title
  type: "pie";          // Chart type (currently only "pie")
}

interface TableSchema {
  key: string;          // Table identifier
  label: string;        // Display title
  layout: "side_by_side_with_chart" | null;  // Layout hint
  columns: TableColumn[];
}

interface TableColumn {
  key: string;          // Column data key (maps to query result fields)
  label: string;        // Column header text
  sortable: boolean;    // Always true — all columns are sortable
}
```

---

## 7. Analytics Query API

### `POST /api/v1/query`

Execute an analytics SQL query. RLS (advertiser_id filtering) is **automatically applied** — the frontend just sends the raw query.

**Headers:** `Authorization: Bearer <token>`, `X-Tenant-ID: <uuid>`

**Request:**
```json
{
  "sql": "SELECT campaign, SUM(impressions) as total_impressions FROM campaign_metrics GROUP BY campaign",
  "params": {}
}
```

**Response:**
```json
{
  "data": [
    { "campaign": "Spring Sale 2026", "total_impressions": 2200000 },
    { "campaign": "Summer Campaign", "total_impressions": 2050000 },
    { "campaign": "Fall Push", "total_impressions": 2140000 }
  ],
  "row_count": 3,
  "cached": false
}
```

**Caching:** Results are cached in Redis for **15 minutes** per tenant + query combination. The `cached: true` flag indicates a cache hit.

**Validation rules:**
- `sql` must be 1–10,000 characters
- Only `SELECT` statements are allowed (INSERT/UPDATE/DELETE/CREATE/DROP rejected → 422)
- SQL injection via OR bypass, subqueries, or UNION is blocked by the RLS injector

**Error responses:**
```json
// 422 - Unsafe SQL
{ "detail": "Unsafe SQL statement type: Delete" }

// 401 - Not authenticated
{ "detail": "Not authenticated" }
```

### Analytics Tables (DuckDB)

The in-memory DuckDB is seeded at startup with dev data. All tables have an `advertiser_id` column for RLS filtering — the frontend never needs to include this in queries; it's injected automatically.

| Table | Dashboard Tab | Key Columns |
|-------|---------------|-------------|
| `campaign_metrics` | Campaign Overview (Overall) | `campaign`, `sub_campaign`, `plan_line_item`, `channel`, `currency`, `spends`, `impressions`, `clicks`, `ctr`, `views`, `vtr`, `conversions`, `cpm`, `cpc` |
| `youtube_metrics` | Campaign Overview (YouTube) | `campaign`, `sub_campaign`, `plan_line_item`, `currency`, `spends`, `impressions`, `views`, `vtr`, `clicks`, `ctr`, `earned_views`, `earned_subscribers` |
| `reach_frequency` | Reach & Frequency | `sub_campaign`, `plan_line_item`, `frequency`, `reach`, `impressions`, `currency`, `spends` |
| `device_metrics` | Device Type | `sub_campaign`, `plan_line_item`, `device_type`, `currency`, `spends`, `impressions`, `clicks`, `ctr`, `views`, `vtr` |
| `geo_region_metrics` | Geo Trends → Region | `sub_campaign`, `plan_line_item`, `region`, `currency`, `spends`, `impressions`, `cpm` |
| `geo_city_metrics` | Geo Trends → City | `sub_campaign`, `plan_line_item`, `city`, `currency`, `spends`, `impressions`, `cpm` |
| `placement_metrics` | Placements | `placement`, `currency`, `spends`, `impressions`, `clicks`, `ctr`, `views`, `vtr`, `cpm` |
| `creative_metrics` | Creative | `sub_campaign`, `plan_line_item`, `creative`, `creative_name`, `format`, `concept`, `size`, `currency`, `spends`, `impressions`, `cpm`, `clicks`, `ctr` |

**Example queries per tab:**

```sql
-- Campaign Overview (Overall)
SELECT campaign, sub_campaign, currency, SUM(spends) as spends, SUM(impressions) as impressions,
       SUM(clicks) as clicks, SUM(views) as views FROM campaign_metrics GROUP BY 1,2,3

-- Device Type pie charts
SELECT device_type, SUM(spends) as value FROM device_metrics GROUP BY device_type

-- Device Type snapshot table
SELECT device_type, currency, SUM(spends) as spends, SUM(impressions) as impressions,
       SUM(clicks) as clicks, ROUND(SUM(clicks)*100.0/SUM(impressions),2) as ctr,
       SUM(views) as views, ROUND(SUM(views)*100.0/SUM(impressions),2) as vtr
FROM device_metrics GROUP BY device_type, currency

-- Geo Trends region pie chart
SELECT region as name, SUM(spends) as value FROM geo_region_metrics GROUP BY region

-- Geo Trends region table
SELECT region, currency, SUM(spends) as spends, SUM(impressions) as impressions,
       ROUND(SUM(spends)/SUM(impressions)*1000,2) as cpm FROM geo_region_metrics GROUP BY region, currency

-- Creative performance table
SELECT creative, creative_name, format, currency, SUM(spends) as spends,
       SUM(impressions) as impressions, ROUND(SUM(spends)/SUM(impressions)*1000,2) as cpm,
       SUM(clicks) as clicks, ROUND(SUM(clicks)*100.0/SUM(impressions),2) as ctr
FROM creative_metrics GROUP BY creative, creative_name, format, currency

-- Filter by sub_campaign (append WHERE clause)
SELECT * FROM device_metrics WHERE sub_campaign = 'Brand Awareness'
```

**Filter values** — to populate filter dropdowns, query distinct values:
```sql
SELECT DISTINCT sub_campaign FROM campaign_metrics
SELECT DISTINCT plan_line_item FROM campaign_metrics
SELECT DISTINCT format FROM creative_metrics
SELECT DISTINCT concept FROM creative_metrics
SELECT DISTINCT size FROM creative_metrics
```

---

## 8. White-Label / Branding API

### `GET /api/v1/whitelabel/config`

Get the tenant's branding configuration. Used on initial app load to theme the UI.

**Headers:** `X-Tenant-ID: <uuid>` (auth optional for public landing pages)

**Response:**
```json
{
  "logo_url": "https://cdn.example.com/acme-logo.png",
  "primary_color": "#FF6B35",
  "secondary_color": "#004E89",
  "custom_css": "body { font-family: 'Inter', sans-serif; }",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Defaults if no branding configured:
```json
{
  "logo_url": null,
  "primary_color": "#000000",
  "secondary_color": "#FFFFFF",
  "custom_css": null,
  "tenant_id": null
}
```

### `PUT /api/v1/whitelabel/config`

Update branding. **Requires `advertiser_admin` role.**

**Headers:** `Authorization: Bearer <token>`, `X-Tenant-ID: <uuid>`

**Request:**
```json
{
  "logo_url": "https://cdn.example.com/new-logo.png",
  "primary_color": "#FF6B35",
  "secondary_color": "#004E89",
  "custom_css": ".dashboard-header { background: linear-gradient(90deg, #FF6B35, #004E89); }"
}
```

**Validation:**
- Colors must be valid 6-digit hex (`#FF0000` — not `red`, not `#FFF`)
- Custom CSS is **sanitized** server-side: `url()`, `@import`, `expression()`, `javascript:`, `behavior:`, `-moz-binding`, `vbscript:` are stripped

**Cache behavior:** Updating branding immediately invalidates the Redis cache for this tenant.

---

## 9. User Management API

### `GET /api/v1/users`

List all users in the current tenant.

**Auth:** `platform_admin` or `advertiser_admin`

**Response:**
```json
[
  {
    "id": "user-uuid-1",
    "tenant_id": "tenant-uuid",
    "email": "alice@acme.com",
    "name": "Alice Johnson",
    "role": "advertiser_admin",
    "auth_provider": "google",
    "is_active": true
  },
  {
    "id": "user-uuid-2",
    "tenant_id": "tenant-uuid",
    "email": "bob@acme.com",
    "name": "Bob Smith",
    "role": "viewer",
    "auth_provider": "google",
    "is_active": true
  }
]
```

### `POST /api/v1/users`

Create a new user in the current tenant.

**Auth:** `advertiser_admin`

**Request:**
```json
{
  "email": "charlie@acme.com",
  "name": "Charlie Brown",
  "role": "analyst"
}
```

**Validation:**
- `email` — must contain `@` and a `.` in the domain, auto-lowercased
- `role` — must be one of: `platform_admin`, `advertiser_admin`, `analyst`, `viewer`
- `name` — 1–255 characters

**Error:** `409 Conflict` if email already exists in this tenant.

### `PATCH /api/v1/users/{user_id}`

Update user name, role, or active status.

**Auth:** `advertiser_admin`

**Request** (all fields optional):
```json
{
  "name": "Charlie B.",
  "role": "viewer",
  "is_active": false
}
```

---

## 10. Tenant Management API

### `POST /api/v1/tenants`

Create a new tenant. **Platform admin only.**

**Request:**
```json
{
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "advertiser_id": "adv_acme_123",
  "dashboard_type": "comprehensive"
}
```

**Validation:**
- `slug` — lowercase alphanumeric + hyphens only (`^[a-z0-9-]+$`), max 100 chars
- `dashboard_type` — must be `"comprehensive"` or `"limited"` (defaults to `"comprehensive"`)
- `name` — 1–255 characters

**Response:** `201 Created`
```json
{
  "id": "tenant-uuid",
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "advertiser_id": "adv_acme_123",
  "dashboard_type": "comprehensive",
  "is_active": true
}
```

**Error:** `409 Conflict` if slug already taken.

### `GET /api/v1/tenants`

List all tenants. **Platform admin only.**

### `GET /api/v1/tenants/{tenant_id}`

Get a specific tenant.

### `PATCH /api/v1/tenants/{tenant_id}`

Update tenant (name, is_active, dashboard_type).

---

## 11. Data Models & Database Schema

### 11.1 Entity Relationship

```
tenants
  ├── 1:1 tenant_branding      (logo, colors, CSS)
  ├── 1:N tenant_domains        (custom domain mappings)
  ├── 1:1 tenant_sso_config     (SSO provider settings)
  ├── 1:N users                  (scoped to tenant)
  └── 1:N rls_policies           (RLS filter rules)
```

### 11.2 Table Schemas

#### `tenants`
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK, auto-generated | |
| `name` | VARCHAR(255) | NOT NULL | Display name |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL | URL-safe identifier |
| `advertiser_id` | VARCHAR(255) | NOT NULL | RLS filter value |
| `dashboard_type` | VARCHAR(20) | NOT NULL | `"comprehensive"` or `"limited"` |
| `is_active` | BOOLEAN | NOT NULL, default `true` | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

#### `users`
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `tenant_id` | UUID | FK → tenants.id CASCADE | |
| `email` | VARCHAR(320) | NOT NULL | |
| `name` | VARCHAR(255) | NOT NULL | |
| `role` | VARCHAR(50) | NOT NULL | `platform_admin`, `advertiser_admin`, `analyst`, `viewer` |
| `auth_provider` | VARCHAR(50) | NOT NULL | `google`, `sso` |
| `is_active` | BOOLEAN | NOT NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

#### `tenant_branding`
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `tenant_id` | UUID | FK → tenants.id CASCADE, UNIQUE | One branding per tenant |
| `logo_url` | VARCHAR(500) | nullable | |
| `primary_color` | VARCHAR(7) | NOT NULL | Hex color `#RRGGBB` |
| `secondary_color` | VARCHAR(7) | NOT NULL | Hex color `#RRGGBB` |
| `custom_css` | TEXT | nullable | Sanitized CSS |
| `created_at` | TIMESTAMPTZ | | |
| `updated_at` | TIMESTAMPTZ | | |

#### `tenant_domains`
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `tenant_id` | UUID | FK → tenants.id CASCADE | |
| `domain` | VARCHAR(255) | UNIQUE, NOT NULL | e.g. `analytics.acme.com` |
| `is_primary` | BOOLEAN | NOT NULL | |

#### `tenant_sso_config`
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `tenant_id` | UUID | FK → tenants.id CASCADE, UNIQUE | |
| `provider` | VARCHAR(50) | NOT NULL | `google`, `okta`, `azure` |
| `client_id` | VARCHAR(500) | NOT NULL | |
| `client_secret_encrypted` | TEXT | NOT NULL | Encrypted at rest |
| `metadata_url` | VARCHAR(500) | nullable | OIDC discovery URL |
| `is_enabled` | BOOLEAN | NOT NULL | |

#### `rls_policies`
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `tenant_id` | UUID | FK → tenants.id CASCADE | |
| `table_name` | VARCHAR(255) | NOT NULL | Analytics table name |
| `filter_column` | VARCHAR(255) | NOT NULL, default `advertiser_id` | |
| `filter_value` | VARCHAR(255) | NOT NULL | Value to filter by |
| `description` | TEXT | nullable | |
| `is_active` | BOOLEAN | NOT NULL | |

---

## 12. Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| `200` | Success | Successful GET/PUT/PATCH |
| `201` | Created | Successful POST (create) |
| `401` | Unauthorized | Missing/invalid/expired JWT token, or tenant not resolved |
| `403` | Forbidden | Valid token but insufficient role |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Duplicate slug, email, etc. |
| `422` | Validation Error | Invalid request body, unsafe SQL |
| `429` | Too Many Requests | Rate limit exceeded (check `Retry-After` header) |

### Pydantic Validation Errors (422)

FastAPI returns detailed field-level errors:
```json
{
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": ["body", "slug"],
      "msg": "String should match pattern '^[a-z0-9-]+$'",
      "input": "Acme Corp"
    }
  ]
}
```

---

## 13. Rate Limiting

| Scope | Limit | Window |
|-------|-------|--------|
| Per user | 100 requests | 1 minute |
| Per tenant | 1,000 requests | 1 minute |

When exceeded, the API returns:
```
HTTP 429 Too Many Requests
Retry-After: 45
```

The `Retry-After` header indicates seconds until the window resets.

Implementation: Redis sorted-set sliding window (each request is a unique entry with a timestamp score).

---

## 14. Middleware Pipeline

Every request passes through this pipeline in order:

```
1. CORS              — Allow cross-origin requests from configured origins
2. Tenant Resolver   — Resolve tenant from hostname/header → request.state.tenant_id
3. Rate Limiter      — Check per-user and per-tenant limits in Redis
4. Auth (JWT)        — Parse Bearer token → request.state.user_id/role/email/tenant_id
5. RLS               — Set request.state.rls_advertiser_id
6. Audit Log         — Log structured JSON: method, path, user, tenant, status, duration_ms
```

**Public paths** that skip tenant resolution: `/docs`, `/openapi.json`, `/health`, `/api/v1/auth/*`

---

## 15. Dashboard Tab Definitions

### Comprehensive Dashboard (6 tabs)

| # | Tab | Sub-tabs | Filters | Charts | Tables |
|---|-----|----------|---------|--------|--------|
| 1 | Campaign Overview | Overall, YouTube | — | — | — |
| 2 | Reach & Frequency | — | Sub Campaign, Plan Line Item | — | — |
| 3 | Device Type | — | Sub Campaign, Plan Line Item | 4 pie charts (Spends, Impressions, Clicks, Views) | Snapshot (8 cols) |
| 4 | Geo Trends | Region, City | Sub Campaign, Plan Line Item (inline) | Spends Share pie (per sub-tab) | Tabular View (5 cols, side-by-side with chart) |
| 5 | Placements | — | — | — | — |
| 6 | Creative | — | Sub Campaign, Plan Line Item, Format, Concept, Size (all inline) | — | Creative Performance (9 cols) |

### Limited Dashboard (3 tabs)

| # | Tab | Same structure as Comprehensive |
|---|-----|------|
| 1 | Campaign Overview | Yes |
| 2 | Geo Trends | Yes |
| 3 | Placements | Yes |

### Table Column Definitions

**Device Type → Snapshot Table:**
| Column Key | Label |
|-----------|-------|
| `device_type` | Device Type |
| `currency` | Currency |
| `spends` | Spends |
| `impressions` | Impressions |
| `clicks` | Clicks |
| `ctr` | CTR |
| `views` | Views |
| `vtr` | VTR |

**Geo Trends → Region/City → Tabular View:**
| Column Key | Label |
|-----------|-------|
| `region` / `city` | Region / City |
| `currency` | Currency |
| `spends` | Spends |
| `impressions` | Impressions |
| `cpm` | CPM |

**Creative → Creative Performance:**
| Column Key | Label |
|-----------|-------|
| `creative` | Creative |
| `creative_name` | Creative Name |
| `format` | Format |
| `currency` | Currency |
| `spends` | Spends |
| `impressions` | Impressions |
| `cpm` | CPM |
| `clicks` | Clicks |
| `ctr` | CTR |

All columns are **sortable**.

---

## 16. Frontend Integration Guide

### 16.1 Initial App Load Sequence

```
1. GET /api/v1/whitelabel/config       → Apply branding (logo, colors, CSS)
     (with X-Tenant-ID header)

2. User authenticates via Google/SSO    → Receive access_token + refresh_token
     POST /api/v1/auth/google/callback

3. GET /api/v1/dashboards              → Render tab navigation and layout
     (with Bearer token + X-Tenant-ID)

4. For each visible tab, fetch data    → POST /api/v1/query with tab-specific SQL
     POST /api/v1/query
```

### 16.2 Token Refresh Strategy

```javascript
// Pseudocode for token refresh
async function fetchWithAuth(url, options) {
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-ID': tenantId,
    }
  });

  if (response.status === 401) {
    // Try refresh
    const refreshResponse = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (refreshResponse.ok) {
      const { access_token, refresh_token } = await refreshResponse.json();
      accessToken = access_token;    // Store new tokens
      refreshToken = refresh_token;

      // Retry original request
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${accessToken}`,
          'X-Tenant-ID': tenantId,
        }
      });
    } else {
      // Redirect to login
      redirectToLogin();
    }
  }

  return response;
}
```

### 16.3 Rendering Dashboard Tabs

```javascript
// Pseudocode for rendering dashboard from API response
const config = await fetchWithAuth('/api/v1/dashboards');

config.tabs.forEach(tab => {
  // Render tab button
  renderTab(tab.key, tab.label, tab.order);

  // When tab is selected:
  if (tab.sub_tabs.length > 0) {
    // Render sub-tab navigation within the tab
    tab.sub_tabs.forEach(subTab => {
      renderSubTab(subTab.key, subTab.label);
      // Charts and tables are inside sub_tabs for Geo Trends
      renderCharts(subTab.charts);  // e.g., pie chart
      renderTables(subTab.tables);  // e.g., tabular view
    });
  }

  // Render filters (dropdowns) at the top of the tab
  if (tab.filters.length > 0) {
    const isInline = tab.filters[0]?.layout === 'inline';
    renderFilters(tab.filters, { inline: isInline });
  }

  // Render charts (top-level, e.g., Device Type pie charts)
  renderCharts(tab.charts);

  // Render tables
  tab.tables.forEach(table => {
    renderSortableTable(table.key, table.label, table.columns);
    // table.layout === 'side_by_side_with_chart' → render next to chart
  });
});
```

### 16.4 Applying White-Label Branding

```javascript
const branding = await fetch('/api/v1/whitelabel/config', {
  headers: { 'X-Tenant-ID': tenantId }
}).then(r => r.json());

// Apply colors as CSS custom properties
document.documentElement.style.setProperty('--primary-color', branding.primary_color);
document.documentElement.style.setProperty('--secondary-color', branding.secondary_color);

// Set logo
if (branding.logo_url) {
  document.getElementById('logo').src = branding.logo_url;
}

// Inject custom CSS (already sanitized by backend)
if (branding.custom_css) {
  const style = document.createElement('style');
  style.textContent = branding.custom_css;
  document.head.appendChild(style);
}
```

### 16.5 Environment Variables for Frontend

```env
REACT_APP_API_BASE_URL=https://api.deepvu.io/api/v1
REACT_APP_DEFAULT_TENANT_ID=<uuid>  # For development only
```

---

*Document version: 1.0 — Generated from DeepVu API source code*
