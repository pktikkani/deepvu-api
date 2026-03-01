import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import patch

import fakeredis.aioredis
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from deepvu.models.base import Base

# Generate ephemeral RSA keys for tests
_test_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_test_public_key = _test_private_key.public_key()

TEST_JWT_PRIVATE_KEY = _test_private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode()

TEST_JWT_PUBLIC_KEY = _test_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def fake_redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def test_settings():
    """Return a dict of overridden settings for tests."""
    return {
        "DATABASE_URL": TEST_DATABASE_URL,
        "REDIS_URL": "redis://fake:6379/0",
        "JWT_PRIVATE_KEY": TEST_JWT_PRIVATE_KEY,
        "JWT_PUBLIC_KEY": TEST_JWT_PUBLIC_KEY,
        "JWT_ALGORITHM": "RS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": 60,
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS": 7,
        "RATE_LIMIT_PER_USER": 100,
        "RATE_LIMIT_PER_TENANT": 1000,
        "CORS_ORIGINS": ["http://localhost:3000"],
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-client-secret",
    }


@pytest.fixture
async def app(db_engine, fake_redis, test_settings):
    # os.environ only accepts str values; convert everything for the env patch
    env_overrides = {k: str(v) for k, v in test_settings.items() if not isinstance(v, list)}
    with patch.dict("os.environ", env_overrides, clear=False):
        from deepvu.config import Settings

        test_cfg = Settings(**test_settings)

        with patch("deepvu.config.settings", test_cfg):
            from deepvu.main import create_app

            application = create_app()

            # Override DB dependency
            session_factory = async_sessionmaker(
                db_engine, class_=AsyncSession, expire_on_commit=False
            )

            async def override_get_db():
                async with session_factory() as session:
                    yield session

            async def override_get_redis():
                return fake_redis

            from deepvu.database import get_db
            from deepvu.redis import get_redis

            application.dependency_overrides[get_db] = override_get_db
            application.dependency_overrides[get_redis] = override_get_redis

            yield application


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
