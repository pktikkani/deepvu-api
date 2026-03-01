import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from deepvu.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False)

    tenant: Mapped["Tenant"] = relationship()  # type: ignore[name-defined]

    def __init__(  # type: ignore[no-untyped-def]
        self,
        *,
        role: str = "viewer",
        auth_provider: str = "google",
        is_active: bool = True,
        **kwargs,
    ):
        super().__init__(
            role=role,
            auth_provider=auth_provider,
            is_active=is_active,
            **kwargs,
        )
