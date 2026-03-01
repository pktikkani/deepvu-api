import uuid

from pydantic import BaseModel, Field, field_validator


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    advertiser_id: str = Field(min_length=1, max_length=255)
    dashboard_type: str = Field(default="comprehensive")

    @field_validator("dashboard_type")
    @classmethod
    def validate_dashboard_type(cls, v: str) -> str:
        if v not in ("comprehensive", "limited"):
            raise ValueError("Must be 'comprehensive' or 'limited'")
        return v


class TenantUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None
    dashboard_type: str | None = None

    @field_validator("dashboard_type")
    @classmethod
    def validate_dashboard_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ("comprehensive", "limited"):
            raise ValueError("Must be 'comprehensive' or 'limited'")
        return v


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    advertiser_id: str
    dashboard_type: str
    is_active: bool

    model_config = {"from_attributes": True}
