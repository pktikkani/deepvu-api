"""Tests for the RLS SQL injector."""

from deepvu.analytics.rls_injector import inject_rls


class TestInjectRLS:
    def test_simple_select(self):
        """A bare SELECT * FROM ads gets a WHERE advertiser_id clause."""
        result = inject_rls("SELECT * FROM ads", "adv1")
        assert "advertiser_id = 'adv1'" in result

    def test_select_with_existing_where(self):
        """Existing WHERE conditions are preserved and ANDed with RLS."""
        result = inject_rls("SELECT * FROM ads WHERE clicks > 100", "adv1")
        assert "advertiser_id = 'adv1'" in result
        assert "clicks > 100" in result

    def test_select_with_join(self):
        """JOINed queries get the advertiser_id filter added."""
        sql = (
            "SELECT * FROM ads "
            "JOIN campaigns ON ads.campaign_id = campaigns.id"
        )
        result = inject_rls(sql, "adv1")
        assert "advertiser_id = 'adv1'" in result

    def test_different_advertiser_ids(self):
        """Different advertiser_id values produce different filters."""
        r1 = inject_rls("SELECT * FROM ads", "adv1")
        r2 = inject_rls("SELECT * FROM ads", "adv2")
        assert "advertiser_id = 'adv1'" in r1
        assert "advertiser_id = 'adv2'" in r2
        assert "adv2" not in r1
        assert "adv1" not in r2
