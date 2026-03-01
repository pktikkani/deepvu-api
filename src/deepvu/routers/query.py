import hashlib
import json

from fastapi import APIRouter, Depends

import redis.asyncio as redis

from deepvu.analytics.protocol import AnalyticsQueryService
from deepvu.dependencies import get_analytics_service, get_current_user, get_tenant_id
from deepvu.exceptions import ValidationError
from deepvu.redis import get_redis
from deepvu.schemas.query import QueryRequest, QueryResponse

router = APIRouter(prefix="/api/v1/query", tags=["query"])

QUERY_CACHE_TTL = 900  # 15 minutes


@router.post("", response_model=QueryResponse)
async def execute_query(
    body: QueryRequest,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
    analytics: AnalyticsQueryService = Depends(get_analytics_service),
    redis_client: redis.Redis = Depends(get_redis),
):
    # Build cache key from tenant + query + params
    cache_key_data = f"{tenant_id}:{body.sql}:{json.dumps(body.params, sort_keys=True)}"
    cache_key = f"query:{hashlib.sha256(cache_key_data.encode()).hexdigest()}"

    # Check cache
    cached = await redis_client.get(cache_key)
    if cached:
        data = json.loads(cached)
        return QueryResponse(data=data, row_count=len(data), cached=True)

    # Resolve advertiser_id from tenant for RLS filtering
    from sqlalchemy import select
    from deepvu.database import get_db
    from deepvu.models.tenant import Tenant

    async for db in get_db():
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise ValidationError("Tenant not found")
        rls_advertiser_id = tenant.advertiser_id
        break

    try:
        data = await analytics.execute_query(body.sql, body.params, rls_advertiser_id)
    except ValueError as e:
        raise ValidationError(str(e))

    # Cache the result
    await redis_client.setex(cache_key, QUERY_CACHE_TTL, json.dumps(data))

    return QueryResponse(data=data, row_count=len(data), cached=False)
