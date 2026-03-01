import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from deepvu.dashboard_config import get_tabs_for_type
from deepvu.database import get_db
from deepvu.dependencies import get_current_user, get_tenant_id
from deepvu.exceptions import NotFoundError
from deepvu.repositories.tenant_repo import TenantRepository
from deepvu.schemas.dashboard import DashboardConfigResponse, DashboardTab

router = APIRouter(prefix="/api/v1/dashboards", tags=["dashboards"])
tenant_repo = TenantRepository()


@router.get("", response_model=DashboardConfigResponse)
async def get_dashboard_config(
    user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    tenant = await tenant_repo.get_by_id(db, tenant_id)
    if not tenant:
        raise NotFoundError("Tenant not found")

    tabs_data = get_tabs_for_type(tenant.dashboard_type)
    tabs = [DashboardTab.model_validate(t) for t in tabs_data]

    return DashboardConfigResponse(
        dashboard_type=tenant.dashboard_type,
        tabs=tabs,
    )
