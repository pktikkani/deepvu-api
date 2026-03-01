import uuid

from pydantic import BaseModel, Field, field_validator

VALID_ROLES = {"platform_admin", "advertiser_admin", "analyst", "viewer"}


class UserCreate(BaseModel):
    email: str = Field(max_length=320)
    name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="viewer")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Basic email validation
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v.lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(sorted(VALID_ROLES))}")
        return v


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    role: str | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(sorted(VALID_ROLES))}")
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    name: str
    role: str
    auth_provider: str
    is_active: bool

    model_config = {"from_attributes": True}
