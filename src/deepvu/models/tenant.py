import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from deepvu.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    advertiser_id: Mapped[str] = mapped_column(String(255), nullable=False)
    dashboard_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "comprehensive" or "limited"
    is_active: Mapped[bool] = mapped_column(nullable=False)

    branding: Mapped["TenantBranding | None"] = relationship(
        back_populates="tenant", uselist=False, cascade="all, delete-orphan"
    )
    domains: Mapped[list["TenantDomain"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    sso_config: Mapped["TenantSSOConfig | None"] = relationship(
        back_populates="tenant", uselist=False, cascade="all, delete-orphan"
    )

    def __init__(self, *, is_active: bool = True, dashboard_type: str = "comprehensive", **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(is_active=is_active, dashboard_type=dashboard_type, **kwargs)


class TenantBranding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenant_branding"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    logo_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str] = mapped_column(String(7), nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(7), nullable=False)
    custom_css: Mapped[str | None] = mapped_column(Text)

    tenant: Mapped["Tenant"] = relationship(back_populates="branding")

    def __init__(  # type: ignore[no-untyped-def]
        self,
        *,
        primary_color: str = "#000000",
        secondary_color: str = "#FFFFFF",
        **kwargs,
    ):
        super().__init__(
            primary_color=primary_color,
            secondary_color=secondary_color,
            **kwargs,
        )


class TenantDomain(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenant_domains"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_primary: Mapped[bool] = mapped_column(nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="domains")

    def __init__(self, *, is_primary: bool = False, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(is_primary=is_primary, **kwargs)


class TenantSSOConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenant_sso_config"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    client_id: Mapped[str] = mapped_column(String(500), nullable=False)
    client_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_url: Mapped[str | None] = mapped_column(String(500))
    is_enabled: Mapped[bool] = mapped_column(nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="sso_config")

    def __init__(self, *, is_enabled: bool = True, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(is_enabled=is_enabled, **kwargs)
