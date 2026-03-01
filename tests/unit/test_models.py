import uuid

from deepvu.models import (
    RLSPolicy,
    Tenant,
    TenantBranding,
    TenantDomain,
    TenantSSOConfig,
    User,
)


class TestTenantModel:
    def test_create_tenant(self):
        t = Tenant(name="Acme Corp", slug="acme", advertiser_id="adv_123")
        assert t.name == "Acme Corp"
        assert t.slug == "acme"
        assert t.advertiser_id == "adv_123"

    def test_tenant_defaults(self):
        t = Tenant(name="Test", slug="test", advertiser_id="adv_1")
        assert t.is_active is True
        assert t.dashboard_type == "comprehensive"

    def test_tenant_dashboard_type_limited(self):
        t = Tenant(name="Test", slug="test", advertiser_id="adv_1", dashboard_type="limited")
        assert t.dashboard_type == "limited"

    def test_tenant_branding(self):
        b = TenantBranding(tenant_id=uuid.uuid4(), primary_color="#FF0000")
        assert b.primary_color == "#FF0000"

    def test_tenant_branding_defaults(self):
        b = TenantBranding(tenant_id=uuid.uuid4())
        assert b.primary_color == "#000000"
        assert b.secondary_color == "#FFFFFF"
        assert b.custom_css is None

    def test_tenant_domain(self):
        d = TenantDomain(tenant_id=uuid.uuid4(), domain="acme.deepvu.io")
        assert d.domain == "acme.deepvu.io"
        assert d.is_primary is False

    def test_tenant_sso_config(self):
        sso = TenantSSOConfig(
            tenant_id=uuid.uuid4(),
            provider="google",
            client_id="cid",
            client_secret_encrypted="encrypted",
        )
        assert sso.provider == "google"
        assert sso.is_enabled is True


class TestUserModel:
    def test_create_user(self):
        u = User(
            tenant_id=uuid.uuid4(),
            email="test@acme.com",
            name="Test User",
            role="viewer",
        )
        assert u.email == "test@acme.com"
        assert u.role == "viewer"

    def test_user_defaults(self):
        u = User(tenant_id=uuid.uuid4(), email="t@t.com", name="T")
        assert u.role == "viewer"
        assert u.auth_provider == "google"
        assert u.is_active is True

    def test_user_roles(self):
        for role in ["platform_admin", "advertiser_admin", "analyst", "viewer"]:
            u = User(tenant_id=uuid.uuid4(), email="t@t.com", name="T", role=role)
            assert u.role == role


class TestRLSPolicyModel:
    def test_create_rls_policy(self):
        p = RLSPolicy(
            tenant_id=uuid.uuid4(),
            table_name="ad_impressions",
            filter_column="advertiser_id",
            filter_value="adv_123",
        )
        assert p.table_name == "ad_impressions"
        assert p.filter_column == "advertiser_id"

    def test_rls_policy_defaults(self):
        p = RLSPolicy(
            tenant_id=uuid.uuid4(),
            table_name="clicks",
            filter_value="adv_1",
        )
        assert p.filter_column == "advertiser_id"
        assert p.is_active is True
        assert p.description is None
