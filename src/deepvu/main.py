from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from deepvu.config import settings
from deepvu.middleware.audit_log import AuditLogMiddleware
from deepvu.middleware.auth import AuthMiddleware
from deepvu.middleware.rate_limiter import RateLimitMiddleware
from deepvu.middleware.rls import RLSMiddleware
from deepvu.middleware.tenant_resolver import TenantResolverMiddleware
from deepvu.redis import close_redis
from deepvu.routers import (
    auth_router,
    dashboards_router,
    query_router,
    tenants_router,
    users_router,
    whitelabel_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    yield
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title="DeepVu API",
        description="Multi-Tenant Ad Analytics Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware stack (order: outermost → innermost)
    # Starlette add_middleware wraps outermost-first (last added = outermost)
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(RLSMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TenantResolverMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    # Register routers
    app.include_router(auth_router)
    app.include_router(tenants_router)
    app.include_router(users_router)
    app.include_router(whitelabel_router)
    app.include_router(dashboards_router)
    app.include_router(query_router)

    return app


app = create_app()
