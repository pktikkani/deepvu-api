import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from deepvu.database import get_db
from deepvu.dependencies import get_tenant_id, require_role
from deepvu.exceptions import ConflictError, NotFoundError
from deepvu.repositories.user_repo import UserRepository
from deepvu.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["users"])
user_repo = UserRepository()


@router.get("", response_model=list[UserResponse])
async def list_users(
    user: dict = Depends(require_role("platform_admin", "advertiser_admin")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return await user_repo.list_by_tenant(db, tenant_id)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    user: dict = Depends(require_role("advertiser_admin")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    existing = await user_repo.get_by_email(db, body.email, tenant_id)
    if existing:
        raise ConflictError(f"User with email '{body.email}' already exists in this tenant")

    user_data = body.model_dump()
    user_data["tenant_id"] = tenant_id
    new_user = await user_repo.create(db, user_data)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdate,
    user: dict = Depends(require_role("advertiser_admin")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        updated = await user_repo.update(
            db, user_id, tenant_id, body.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise NotFoundError("User not found")
    await db.commit()
    await db.refresh(updated)
    return updated
