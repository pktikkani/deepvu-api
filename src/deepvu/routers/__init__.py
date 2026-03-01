from deepvu.routers.auth import router as auth_router
from deepvu.routers.dashboards import router as dashboards_router
from deepvu.routers.query import router as query_router
from deepvu.routers.tenants import router as tenants_router
from deepvu.routers.users import router as users_router
from deepvu.routers.whitelabel import router as whitelabel_router

__all__ = [
    "auth_router",
    "dashboards_router",
    "query_router",
    "tenants_router",
    "users_router",
    "whitelabel_router",
]
