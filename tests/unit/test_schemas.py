import uuid

import pytest
from pydantic import ValidationError

from deepvu.schemas.dashboard import DashboardConfigResponse, DashboardTab
from deepvu.schemas.query import QueryRequest
from deepvu.schemas.tenant import TenantCreate
from deepvu.schemas.user import UserCreate
from deepvu.schemas.whitelabel import WhitelabelConfig


class TestTenantSchemas:
    def test_tenant_create_valid(self) -> None:
        tenant = TenantCreate(
            name="Acme Corp",
            slug="acme-corp",
            advertiser_id="adv-123",
            dashboard_type="comprehensive",
        )
        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme-corp"
        assert tenant.advertiser_id == "adv-123"
        assert tenant.dashboard_type == "comprehensive"

    def test_tenant_create_invalid_slug(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(
                name="Acme Corp",
                slug="acme corp",  # spaces not allowed
                advertiser_id="adv-123",
            )
        assert "slug" in str(exc_info.value).lower() or "pattern" in str(exc_info.value).lower()

    def test_tenant_create_invalid_dashboard_type(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(
                name="Acme Corp",
                slug="acme-corp",
                advertiser_id="adv-123",
                dashboard_type="premium",
            )
        assert "comprehensive" in str(exc_info.value) or "limited" in str(exc_info.value)


class TestUserSchemas:
    def test_user_create_valid(self) -> None:
        user = UserCreate(
            email="alice@example.com",
            name="Alice Smith",
            role="analyst",
        )
        assert user.email == "alice@example.com"
        assert user.name == "Alice Smith"
        assert user.role == "analyst"

    def test_user_create_invalid_email(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="not-an-email",
                name="Alice Smith",
                role="viewer",
            )
        assert "email" in str(exc_info.value).lower()

    def test_user_create_invalid_role(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="alice@example.com",
                name="Alice Smith",
                role="superadmin",
            )
        assert "role" in str(exc_info.value).lower() or "Role" in str(exc_info.value)


class TestWhitelabelSchemas:
    def test_whitelabel_valid_colors(self) -> None:
        config = WhitelabelConfig(
            primary_color="#FF0000",
            secondary_color="#00FF00",
        )
        assert config.primary_color == "#FF0000"
        assert config.secondary_color == "#00FF00"

    def test_whitelabel_invalid_color(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            WhitelabelConfig(
                primary_color="red",
            )
        assert "hex color" in str(exc_info.value).lower() or "color" in str(exc_info.value).lower()


class TestQuerySchemas:
    def test_query_request_valid(self) -> None:
        query = QueryRequest(
            sql="SELECT * FROM campaigns WHERE advertiser_id = :adv_id",
            params={"adv_id": "123"},
        )
        assert query.sql.startswith("SELECT")
        assert query.params == {"adv_id": "123"}


class TestDashboardSchemas:
    def test_dashboard_tab_response(self) -> None:
        from deepvu.schemas.dashboard import SubTab, FilterConfig, ChartConfig

        response = DashboardConfigResponse(
            dashboard_type="comprehensive",
            tabs=[
                DashboardTab(
                    key="campaign_overview",
                    label="Campaign Overview",
                    order=1,
                    sub_tabs=[
                        SubTab(key="overall", label="Overall"),
                        SubTab(key="youtube", label="YouTube"),
                    ],
                ),
                DashboardTab(
                    key="device_type",
                    label="Device Type",
                    order=2,
                    filters=[FilterConfig(key="sub_campaign", label="Sub Campaign")],
                    charts=[ChartConfig(key="spends", label="Spends", type="pie")],
                ),
            ],
        )
        assert response.dashboard_type == "comprehensive"
        assert len(response.tabs) == 2
        assert response.tabs[0].key == "campaign_overview"
        assert len(response.tabs[0].sub_tabs) == 2
        assert response.tabs[1].filters[0].key == "sub_campaign"
        assert response.tabs[1].charts[0].type == "pie"

        # Verify serialization
        data = response.model_dump()
        assert data["dashboard_type"] == "comprehensive"
        assert len(data["tabs"]) == 2
        assert data["tabs"][0]["sub_tabs"][0]["key"] == "overall"
