from deepvu.config import Settings


class TestSettings:
    def test_default_database_url(self):
        s = Settings(
            DATABASE_URL="postgresql+asyncpg://deepvu:deepvu_dev@localhost:5432/deepvu",
            JWT_PRIVATE_KEY="",
            JWT_PUBLIC_KEY="",
        )
        assert "asyncpg" in s.DATABASE_URL

    def test_default_redis_url(self):
        s = Settings(JWT_PRIVATE_KEY="", JWT_PUBLIC_KEY="")
        assert s.REDIS_URL == "redis://localhost:6379/0"

    def test_default_jwt_algorithm(self):
        s = Settings(JWT_PRIVATE_KEY="", JWT_PUBLIC_KEY="")
        assert s.JWT_ALGORITHM == "RS256"

    def test_default_rate_limits(self):
        s = Settings(JWT_PRIVATE_KEY="", JWT_PUBLIC_KEY="")
        assert s.RATE_LIMIT_PER_USER == 100
        assert s.RATE_LIMIT_PER_TENANT == 1000

    def test_default_token_expiry(self):
        s = Settings(JWT_PRIVATE_KEY="", JWT_PUBLIC_KEY="")
        assert s.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert s.JWT_REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_default_cors_origins(self):
        s = Settings(JWT_PRIVATE_KEY="", JWT_PUBLIC_KEY="")
        assert "http://localhost:3000" in s.CORS_ORIGINS

    def test_custom_settings(self):
        s = Settings(
            DATABASE_URL="postgresql+asyncpg://custom:5432/db",
            REDIS_URL="redis://custom:6379/1",
            JWT_PRIVATE_KEY="pk",
            JWT_PUBLIC_KEY="pub",
            RATE_LIMIT_PER_USER=50,
        )
        assert s.RATE_LIMIT_PER_USER == 50
        assert "custom" in s.DATABASE_URL
