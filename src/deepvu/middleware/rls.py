from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RLSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Set RLS advertiser_id from the tenant context
        # This will be used by the analytics query layer
        request.state.rls_advertiser_id = None

        # The actual advertiser_id will be resolved by the dependency layer
        # based on the tenant's configuration

        return await call_next(request)
