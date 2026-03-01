import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as redis

from deepvu.database import get_db
from deepvu.dependencies import get_tenant_id, require_role
from deepvu.repositories.tenant_repo import TenantRepository
from deepvu.schemas.whitelabel import WhitelabelConfig, WhitelabelResponse
from deepvu.services.css_sanitizer import sanitize_css
from deepvu.redis import get_redis

router = APIRouter(prefix="/api/v1/whitelabel", tags=["whitelabel"])
tenant_repo = TenantRepository()


@router.get("/config", response_model=WhitelabelResponse)
async def get_whitelabel_config(
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    # Try cache first
    cached = await redis_client.get(f"whitelabel:{tenant_id}")
    if cached:
        import json

        return WhitelabelResponse(**json.loads(cached))

    branding = await tenant_repo.get_branding(db, tenant_id)
    if branding is None:
        return WhitelabelResponse()

    response = WhitelabelResponse(
        logo_url=branding.logo_url,
        primary_color=branding.primary_color,
        secondary_color=branding.secondary_color,
        custom_css=branding.custom_css,
        tenant_id=str(branding.tenant_id),
    )

    # Cache for 5 minutes
    import json

    await redis_client.setex(
        f"whitelabel:{tenant_id}", 300, json.dumps(response.model_dump())
    )

    return response


@router.put("/config", response_model=WhitelabelResponse)
async def update_whitelabel_config(
    body: WhitelabelConfig,
    user: dict = Depends(require_role("advertiser_admin")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    data = body.model_dump()

    # Sanitize custom CSS
    if data.get("custom_css"):
        data["custom_css"] = sanitize_css(data["custom_css"])

    branding = await tenant_repo.get_branding(db, tenant_id)
    if branding is None:
        branding = await tenant_repo.create_branding(db, tenant_id, data)
    else:
        branding = await tenant_repo.update_branding(db, tenant_id, data)

    await db.commit()
    await db.refresh(branding)

    # Invalidate cache
    await redis_client.delete(f"whitelabel:{tenant_id}")

    return WhitelabelResponse(
        logo_url=branding.logo_url,
        primary_color=branding.primary_color,
        secondary_color=branding.secondary_color,
        custom_css=branding.custom_css,
        tenant_id=str(branding.tenant_id),
    )
