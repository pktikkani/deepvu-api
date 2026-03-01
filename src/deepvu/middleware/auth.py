import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from deepvu.auth.jwt_handler import decode_access_token

PUBLIC_PATHS = {
    "/docs",
    "/openapi.json",
    "/health",
    "/api/v1/auth/google/callback",
    "/api/v1/auth/sso/callback",
    "/api/v1/auth/refresh",
    "/api/v1/whitelabel/config",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # For purely static/docs paths and OPTIONS, skip token parsing entirely
        if request.url.path.startswith("/docs") or request.method == "OPTIONS":
            return await call_next(request)

        # Always attempt to extract and decode a token (even on public paths)
        # so that endpoints requiring auth on otherwise-public routes can work.
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if token is None:
            token = request.cookies.get("access_token")

        if token:
            try:
                payload = decode_access_token(token)
                request.state.user_id = payload["sub"]
                request.state.user_email = payload.get("email", "")
                request.state.user_role = payload["role"]
                request.state.user_tenant_id = payload["tenant_id"]
            except (jwt.PyJWTError, KeyError):
                pass  # Leave user info unset; dependency checks will handle auth

        return await call_next(request)
