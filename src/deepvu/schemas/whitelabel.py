import re

from pydantic import BaseModel, Field, field_validator

HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


class WhitelabelConfig(BaseModel):
    logo_url: str | None = None
    primary_color: str = Field(default="#000000")
    secondary_color: str = Field(default="#FFFFFF")
    custom_css: str | None = None

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not HEX_COLOR_PATTERN.match(v):
            raise ValueError("Must be a valid hex color (e.g., #FF0000)")
        return v


class WhitelabelResponse(WhitelabelConfig):
    tenant_id: str | None = None

    model_config = {"from_attributes": True}
