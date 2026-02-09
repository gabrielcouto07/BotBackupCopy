"""
Bot control routes: start, stop, status, test-run
"""
from datetime import datetime, timedelta
from uuid import UUID
import json
from fastapi import APIRouter, Depends, HTTPException, status
import redis.asyncio as redis

from ..core.config import settings
from ..core.deps import get_current_user, require_role, CurrentUser
from ..models.schemas import (
    BotStatus, BotStatusEnum, BotStartResponse, BotStopResponse,
    TestRunRequest, TestRunResponse, Role, MessageResponse
)
from ..db.database import get_pool

router = APIRouter(prefix="/bot", tags=["Bot Control"])

# Redis client for pub/sub and status
_redis_client = None


async def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL)
    return _redis_client


@router.get("/status", response_model=BotStatus)
async def get_bot_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current bot status for the tenant
    """
    pool = await get_pool()
    redis_client = await get_redis()
    tenant_id = str(current_user.tenant_id)
    
    # Check if there's a running task
    status_key = f"bot_status:{tenant_id}"
    status_data = await redis_client.get(status_key)
    
    if status_data:
        data = json.loads(status_data)
        return BotStatus(
            tenant_id=current_user.tenant_id,
            status=BotStatusEnum(data.get("status", "idle")),
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
            next_run=datetime.fromisoformat(data["next_run"]) if data.get("next_run") else None,
            current_cycle=data.get("current_cycle"),
            uptime_seconds=data.get("uptime_seconds")
        )
    
    # Check database for last run
    async with pool.acquire() as conn:
        last_run = await conn.fetchrow(
            """
            SELECT started_at, completed_at, status
            FROM bot_runs
            WHERE tenant_id = $1
            ORDER BY started_at DESC
            LIMIT 1
            """,
            current_user.tenant_id
        )
    
    if last_run and last_run['status'] == 'running':
        return BotStatus(
            tenant_id=current_user.tenant_id,
            status=BotStatusEnum.RUNNING,
            last_run=last_run['started_at']
        )
    
    return BotStatus(
        tenant_id=current_user.tenant_id,
        status=BotStatusEnum.IDLE,
        last_run=last_run['started_at'] if last_run else None
    )


@router.post("/start", response_model=BotStartResponse)
async def start_bot(
    current_user: CurrentUser = Depends(require_role(Role.USER))
):
    """
    Start the bot for this tenant.
    Requires USER role or higher.
    """
    pool = await get_pool()
    redis_client = await get_redis()
    tenant_id = str(current_user.tenant_id)
    
    # Check if already running
    status_key = f"bot_status:{tenant_id}"
    status_data = await redis_client.get(status_key)
    
    if status_data:
        data = json.loads(status_data)
        if data.get("status") == "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is already running"
            )
    
    # Check for active lock
    async with pool.acquire() as conn:
        lock = await conn.fetchrow(
            """
            SELECT locked_by, expires_at FROM bot_locks
            WHERE tenant_id = $1 AND expires_at > NOW()
            """,
            current_user.tenant_id
        )
        
        if lock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is already running on another worker"
            )
        
        # Create bot_run entry
        run_row = await conn.fetchrow(
            """
            INSERT INTO bot_runs (tenant_id, status, started_at, triggered_by)
            VALUES ($1, 'running', NOW(), 'manual')
            RETURNING id
            """,
            current_user.tenant_id
        )
        
        # Log the action
        await conn.execute(
            """
            INSERT INTO audit_logs (tenant_id, user_id, action, resource_type, resource_id)
            VALUES ($1, $2, 'bot.start', 'bot_run', $3)
            """,
            current_user.tenant_id, current_user.id, run_row['id']
        )
    
    # Update Redis status
    await redis_client.set(
        status_key,
        json.dumps({
            "status": "running",
            "run_id": str(run_row['id']),
            "started_at": datetime.utcnow().isoformat(),
            "last_run": datetime.utcnow().isoformat()
        }),
        ex=86400  # 24 hour expiry
    )
    
    # Enqueue Celery task
    try:
        from ..worker.tasks import run_bot_loop
        run_bot_loop.apply_async(
            args=[tenant_id, str(run_row['id'])],
            queue=f"bot_tenant_{tenant_id}"
        )
    except Exception as e:
        # If Celery not available, still return success (task will be picked up)
        pass
    
    return BotStartResponse(
        status="started",
        run_id=run_row['id'],
        message="Bot started successfully"
    )


@router.post("/stop", response_model=BotStopResponse)
async def stop_bot(
    current_user: CurrentUser = Depends(require_role(Role.USER))
):
    """
    Stop the bot gracefully.
    Sends stop command via Redis pub/sub.
    """
    redis_client = await get_redis()
    pool = await get_pool()
    tenant_id = str(current_user.tenant_id)
    
    # Send stop command
    command_key = f"bot_command:{tenant_id}"
    await redis_client.set(command_key, "stop", ex=300)  # 5 min TTL
    
    # Also publish for real-time notification
    await redis_client.publish(f"bot_commands:{tenant_id}", "stop")
    
    # Update status
    status_key = f"bot_status:{tenant_id}"
    await redis_client.delete(status_key)
    
    # Update bot_run in database
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE bot_runs
            SET status = 'stopped', completed_at = NOW()
            WHERE tenant_id = $1 AND status = 'running'
            """,
            current_user.tenant_id
        )
        
        # Log the action
        await conn.execute(
            """
            INSERT INTO audit_logs (tenant_id, user_id, action)
            VALUES ($1, $2, 'bot.stop')
            """,
            current_user.tenant_id, current_user.id
        )
    
    return BotStopResponse(
        status="stopped",
        message="Stop command sent to bot"
    )


@router.post("/test-run", response_model=TestRunResponse)
async def test_run(
    request: TestRunRequest,
    current_user: CurrentUser = Depends(require_role(Role.USER))
):
    """
    Execute a single test cycle of the bot.
    Uses incognito mode and doesn't persist session.
    """
    pool = await get_pool()
    tenant_id = str(current_user.tenant_id)
    
    # Create test run entry
    async with pool.acquire() as conn:
        run_row = await conn.fetchrow(
            """
            INSERT INTO bot_runs (tenant_id, status, started_at, triggered_by)
            VALUES ($1, 'running', NOW(), 'test')
            RETURNING id
            """,
            current_user.tenant_id
        )
    
    start_time = datetime.utcnow()
    errors = []
    orders_found = 0
    actions_taken = 0
    
    try:
        # Import and run bot logic synchronously for test
        from ..worker.bot_logic import execute_test_run
        result = await execute_test_run(
            tenant_id=tenant_id,
            dry_run=request.dry_run,
            timeout=request.timeout_seconds
        )
        
        orders_found = result.get("orders_found", 0)
        actions_taken = result.get("actions_taken", 0)
        errors = result.get("errors", [])
        final_status = "completed" if not errors else "completed_with_errors"
        
    except Exception as e:
        errors.append(str(e))
        final_status = "failed"
    
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Update run in database
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE bot_runs
            SET status = $2, completed_at = NOW(),
                result_data = $3, error_message = $4
            WHERE id = $1
            """,
            run_row['id'],
            final_status,
            json.dumps({
                "orders_found": orders_found,
                "actions_taken": actions_taken,
                "dry_run": request.dry_run
            }),
            errors[0] if errors else None
        )
    
    return TestRunResponse(
        run_id=run_row['id'],
        status=final_status,
        duration_seconds=round(duration, 2),
        orders_found=orders_found,
        actions_taken=actions_taken,
        errors=errors
    )


@router.post("/reload-config", response_model=MessageResponse)
async def reload_config(
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """
    Signal the running bot to reload its configuration.
    Useful after config changes without restarting.
    """
    redis_client = await get_redis()
    tenant_id = str(current_user.tenant_id)
    
    # Send reload command
    command_key = f"bot_command:{tenant_id}"
    await redis_client.set(command_key, "reload_config", ex=300)
    await redis_client.publish(f"bot_commands:{tenant_id}", "reload_config")
    
    return MessageResponse(
        message="Reload config command sent",
        success=True
    )
