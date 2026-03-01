from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from deepvu.database import get_db
from deepvu.dependencies import require_role
from deepvu.exceptions import ConflictError, NotFoundError
from deepvu.repositories.tenant_repo import TenantRepository
from deepvu.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])
tenant_repo = TenantRepository()


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    body: TenantCreate,
    user: dict = Depends(require_role("platform_admin")),
    db: AsyncSession = Depends(get_db),
):
    existing = await tenant_repo.get_by_slug(db, body.slug)
    if existing:
        raise ConflictError(f"Tenant with slug '{body.slug}' already exists")

    tenant = await tenant_repo.create(db, body.model_dump())
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    user: dict = Depends(require_role("platform_admin")),
    db: AsyncSession = Depends(get_db),
):
    return await tenant_repo.list_all(db)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    user: dict = Depends(require_role("platform_admin")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await tenant_repo.get_by_id(db, tenant_id)
    if not tenant:
        raise NotFoundError("Tenant not found")
    return tenant


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    body: TenantUpdate,
    user: dict = Depends(require_role("platform_admin")),
    db: AsyncSession = Depends(get_db),
):
    try:
        tenant = await tenant_repo.update(
            db, tenant_id, body.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise NotFoundError("Tenant not found")
    await db.commit()
    await db.refresh(tenant)
    return tenant
