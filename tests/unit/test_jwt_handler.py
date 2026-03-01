import time
import uuid
from datetime import timedelta
from unittest.mock import patch

import jwt as pyjwt
import pytest

from deepvu.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    revoke_refresh_token,
    rotate_refresh_token,
)
from tests.conftest import TEST_JWT_PRIVATE_KEY, TEST_JWT_PUBLIC_KEY


@pytest.fixture(autouse=True)
def _patch_settings():
    with patch("deepvu.auth.jwt_handler.settings") as mock_settings:
        mock_settings.JWT_PRIVATE_KEY = TEST_JWT_PRIVATE_KEY
        mock_settings.JWT_PUBLIC_KEY = TEST_JWT_PUBLIC_KEY
        mock_settings.JWT_ALGORITHM = "RS256"
        mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
        mock_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
        yield mock_settings


class TestAccessToken:
    def test_encode_decode_roundtrip(self):
        token = create_access_token(
            user_id="user-1", tenant_id="tenant-1", role="viewer", email="a@b.com"
        )
        payload = decode_access_token(token)
        assert payload["sub"] == "user-1"
        assert payload["tenant_id"] == "tenant-1"
        assert payload["role"] == "viewer"
        assert payload["email"] == "a@b.com"
        assert payload["type"] == "access"

    def test_rs256_algorithm(self):
        token = create_access_token(
            user_id="u", tenant_id="t", role="viewer", email="a@b.com"
        )
        header = pyjwt.get_unverified_header(token)
        assert header["alg"] == "RS256"

    def test_token_has_expiry(self):
        token = create_access_token(
            user_id="u", tenant_id="t", role="viewer", email="a@b.com"
        )
        payload = decode_access_token(token)
        assert "exp" in payload
        assert "iat" in payload

    def test_expired_token_rejected(self):
        token = create_access_token(
            user_id="u",
            tenant_id="t",
            role="viewer",
            email="a@b.com",
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_tampered_token_rejected(self):
        token = create_access_token(
            user_id="u", tenant_id="t", role="viewer", email="a@b.com"
        )
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(pyjwt.InvalidSignatureError):
            decode_access_token(tampered)

    def test_custom_expiry(self):
        token = create_access_token(
            user_id="u",
            tenant_id="t",
            role="viewer",
            email="a@b.com",
            expires_delta=timedelta(minutes=5),
        )
        payload = decode_access_token(token)
        # exp - iat should be ~5 minutes
        diff = payload["exp"] - payload["iat"]
        assert 290 <= diff <= 310  # ~5 min with some tolerance


class TestRefreshToken:
    async def test_create_refresh_token(self, fake_redis):
        token = await create_refresh_token("user-1", fake_redis)
        assert isinstance(token, str)
        # Token should be stored in redis
        stored = await fake_redis.get(f"refresh:{token}")
        assert stored == "user-1"

    async def test_rotate_refresh_token(self, fake_redis):
        old_token = await create_refresh_token("user-1", fake_redis)
        new_token, user_id = await rotate_refresh_token(old_token, fake_redis)

        assert user_id == "user-1"
        assert new_token != old_token

        # Old token consumed
        assert await fake_redis.get(f"refresh:{old_token}") is None
        # New token exists
        assert await fake_redis.get(f"refresh:{new_token}") == "user-1"

    async def test_reuse_rejected(self, fake_redis):
        old_token = await create_refresh_token("user-1", fake_redis)
        await rotate_refresh_token(old_token, fake_redis)

        # Reusing the old token should fail
        with pytest.raises(ValueError, match="Invalid or expired refresh token"):
            await rotate_refresh_token(old_token, fake_redis)

    async def test_revoke_refresh_token(self, fake_redis):
        token = await create_refresh_token("user-1", fake_redis)
        await revoke_refresh_token(token, fake_redis)
        assert await fake_redis.get(f"refresh:{token}") is None

    async def test_expired_refresh_rejected(self, fake_redis):
        with pytest.raises(ValueError, match="Invalid or expired refresh token"):
            await rotate_refresh_token("nonexistent-token", fake_redis)
