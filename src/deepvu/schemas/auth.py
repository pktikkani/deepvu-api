from pydantic import BaseModel


class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


class SSOCallbackRequest(BaseModel):
    code: str
    state: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
