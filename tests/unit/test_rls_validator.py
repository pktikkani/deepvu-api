"""Tests for the RLS validator and SQL safety checks."""

import pytest

from deepvu.analytics.rls_injector import inject_rls
from deepvu.analytics.rls_validator import reject_unsafe_sql, validate_rls


class TestValidateRLS:
    def test_valid_rls(self):
        """After injection, validate_rls returns True."""
        secured = inject_rls("SELECT * FROM ads", "adv1")
        assert validate_rls(secured, "adv1") is True

    def test_missing_rls(self):
        """A raw query without injection returns False."""
        assert validate_rls("SELECT * FROM ads", "adv1") is False


class TestRejectUnsafeSQL:
    def test_reject_insert(self):
        with pytest.raises(ValueError, match="Insert"):
            reject_unsafe_sql("INSERT INTO ads VALUES (1, 'adv1', 'camp', 10)")

    def test_reject_update(self):
        with pytest.raises(ValueError, match="Update"):
            reject_unsafe_sql("UPDATE ads SET clicks = 0")

    def test_reject_delete(self):
        with pytest.raises(ValueError, match="Delete"):
            reject_unsafe_sql("DELETE FROM ads")

    def test_reject_create(self):
        with pytest.raises(ValueError, match="Create"):
            reject_unsafe_sql("CREATE TABLE evil (id INT)")

    def test_reject_drop(self):
        with pytest.raises(ValueError, match="Drop"):
            reject_unsafe_sql("DROP TABLE ads")

    def test_allow_select(self):
        """SELECT statements should not raise."""
        reject_unsafe_sql("SELECT * FROM ads")
