import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from deepvu.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RLSPolicy(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "rls_policies"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    filter_column: Mapped[str] = mapped_column(String(255), nullable=False)
    filter_value: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(nullable=False)

    tenant: Mapped["Tenant"] = relationship()  # type: ignore[name-defined]

    def __init__(  # type: ignore[no-untyped-def]
        self,
        *,
        filter_column: str = "advertiser_id",
        is_active: bool = True,
        **kwargs,
    ):
        super().__init__(
            filter_column=filter_column,
            is_active=is_active,
            **kwargs,
        )
