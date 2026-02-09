"""
Health check and metrics routes
"""
from fastapi import APIRouter
import redis.asyncio as redis

from ..core.config import settings
from ..db.database import get_pool
from ..models.schemas import HealthCheckResponse, MetricsResponse

router = APIRouter(tags=["Health & Metrics"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint for load balancer and monitoring.
    """
    db_status = "error"
    redis_status = "error"
    
    # Check database
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "ok"
    except Exception as e:
        pass
    
    # Check Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        redis_status = "ok"
    except Exception:
        pass
    
    status = "healthy" if db_status == "ok" and redis_status == "ok" else "unhealthy"
    
    return HealthCheckResponse(
        status=status,
        database=db_status,
        redis=redis_status,
        version=settings.APP_VERSION
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get system metrics for monitoring dashboards.
    """
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        # Active bots (running status)
        active_bots = await conn.fetchval(
            "SELECT COUNT(*) FROM bot_runs WHERE status = 'running'"
        ) or 0
        
        # Total runs today
        runs_today = await conn.fetchval(
            """
            SELECT COUNT(*) FROM bot_runs
            WHERE started_at >= CURRENT_DATE
            """
        ) or 0
        
        # Total tenants
        total_tenants = await conn.fetchval(
            "SELECT COUNT(*) FROM tenants WHERE is_active = TRUE"
        ) or 0
        
        # Total users
        total_users = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE is_active = TRUE"
        ) or 0
    
    # Pending tasks in Redis
    pending_tasks = 0
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        pending_tasks = await redis_client.llen("celery") or 0
        await redis_client.close()
    except Exception:
        pass
    
    return MetricsResponse(
        active_bots=active_bots,
        pending_tasks=pending_tasks,
        total_runs_today=runs_today,
        total_tenants=total_tenants,
        total_users=total_users
    )
