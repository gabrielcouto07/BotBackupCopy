"""
Celery tasks for bot workers
"""
import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from uuid import UUID
from celery import Celery
import redis
import asyncpg
from playwright.async_api import async_playwright

from .session_manager import TenantSessionManager
from .config_loader import TenantConfigLoader, ConfigCache
from .browser_config import create_browser_context
from .bot_logic import execute_bot_logic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Celery app
app = Celery('bot_worker')
app.config_from_object('app.worker.celery_config')

# Database and Redis URLs from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/bot_saas"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def get_db_pool():
    """Create database connection pool"""
    return await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)


def get_redis_client():
    """Get Redis client"""
    return redis.from_url(REDIS_URL)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_bot_loop(self, tenant_id: str, run_id: str):
    """
    Main task that runs the bot loop for a tenant.
    
    Args:
        tenant_id: Tenant identifier
        run_id: Bot run identifier
    """
    return asyncio.run(_async_bot_loop(self, tenant_id, run_id))


async def _async_bot_loop(task, tenant_id: str, run_id: str):
    """
    Async implementation of the bot loop.
    """
    pool = await get_db_pool()
    redis_client = get_redis_client()
    session_manager = TenantSessionManager()
    config_loader = TenantConfigLoader(pool)
    
    logger.info(f"[{tenant_id}] Starting bot loop, run_id={run_id}")
    
    # Acquire lock
    lock_acquired = await acquire_tenant_lock(pool, tenant_id, task.request.id)
    if not lock_acquired:
        logger.warning(f"[{tenant_id}] Lock already held, aborting")
        return {"status": "skipped", "reason": "already_running"}
    
    try:
        # Load config
        config = await config_loader.get_tenant_config(tenant_id)
        secrets = await config_loader.get_tenant_secrets(tenant_id)
        
        # Session paths
        storage_state_path = str(session_manager.get_storage_state_path(tenant_id))
        
        # Start Playwright
        async with async_playwright() as p:
            browser, context = await create_browser_context(
                p,
                tenant_id,
                storage_state_path if session_manager.session_exists(tenant_id) else None,
                headless=config.get('headless', True)
            )
            
            page = await context.new_page()
            
            should_continue = True
            cycle_count = 0
            
            while should_continue:
                cycle_count += 1
                logger.info(f"[{tenant_id}] Cycle {cycle_count} starting")
                
                # Update status in Redis
                await update_bot_status(redis_client, tenant_id, run_id, "running", cycle_count)
                
                try:
                    # Execute bot logic
                    result = await execute_bot_logic(
                        page=page,
                        config=config,
                        secrets=secrets,
                        tenant_id=tenant_id,
                        session_manager=session_manager
                    )
                    
                    # Save result
                    await save_cycle_result(pool, tenant_id, run_id, cycle_count, result)
                    
                    # Persist session
                    await context.storage_state(path=storage_state_path)
                    
                    logger.info(f"[{tenant_id}] Cycle {cycle_count} completed: {result}")
                    
                except Exception as e:
                    logger.exception(f"[{tenant_id}] Cycle {cycle_count} error: {e}")
                    await log_error(pool, tenant_id, run_id, str(e))
                    
                    max_retries = config.get('max_retries', 3)
                    if cycle_count >= max_retries:
                        logger.error(f"[{tenant_id}] Max retries reached, stopping")
                        break
                    
                    await asyncio.sleep(60)
                    continue
                
                # Check for commands
                command = check_redis_command(redis_client, tenant_id)
                if command == "stop":
                    logger.info(f"[{tenant_id}] Stop command received")
                    should_continue = False
                elif command == "reload_config":
                    logger.info(f"[{tenant_id}] Reloading config")
                    config = await config_loader.get_tenant_config(tenant_id)
                    secrets = await config_loader.get_tenant_secrets(tenant_id)
                
                # Check if tenant is still active
                if not await config_loader.is_tenant_active(tenant_id):
                    logger.warning(f"[{tenant_id}] Tenant deactivated, stopping")
                    should_continue = False
                
                if should_continue:
                    # Wait for next cycle
                    interval = config.get('check_interval_minutes', 15) * 60
                    logger.info(f"[{tenant_id}] Waiting {interval}s until next cycle")
                    await asyncio.sleep(interval)
            
            await browser.close()
        
        # Mark run as completed
        await mark_run_completed(pool, run_id, cycle_count)
        
        return {"status": "completed", "cycles": cycle_count}
        
    except Exception as e:
        logger.exception(f"[{tenant_id}] Fatal error: {e}")
        await mark_run_failed(pool, run_id, str(e))
        raise task.retry(exc=e)
        
    finally:
        # Release lock
        await release_tenant_lock(pool, tenant_id)
        # Clear Redis status
        redis_client.delete(f"bot_status:{tenant_id}")
        await pool.close()


async def acquire_tenant_lock(pool: asyncpg.Pool, tenant_id: str, worker_id: str) -> bool:
    """Acquire distributed lock for tenant"""
    query = """
        INSERT INTO bot_locks (tenant_id, locked_by, expires_at)
        VALUES ($1, $2, NOW() + INTERVAL '1 hour')
        ON CONFLICT (tenant_id) 
        DO UPDATE SET locked_by = $2, locked_at = NOW(), expires_at = NOW() + INTERVAL '1 hour'
        WHERE bot_locks.expires_at < NOW()
        RETURNING tenant_id
    """
    async with pool.acquire() as conn:
        result = await conn.fetchrow(query, UUID(tenant_id), worker_id)
    return result is not None


async def release_tenant_lock(pool: asyncpg.Pool, tenant_id: str):
    """Release tenant lock"""
    query = "DELETE FROM bot_locks WHERE tenant_id = $1"
    async with pool.acquire() as conn:
        await conn.execute(query, UUID(tenant_id))


def check_redis_command(redis_client, tenant_id: str) -> str | None:
    """Check for pending commands in Redis"""
    key = f"bot_command:{tenant_id}"
    command = redis_client.get(key)
    if command:
        redis_client.delete(key)
        return command.decode()
    return None


async def update_bot_status(redis_client, tenant_id: str, run_id: str, status: str, cycle: int):
    """Update bot status in Redis"""
    key = f"bot_status:{tenant_id}"
    data = {
        "status": status,
        "run_id": run_id,
        "current_cycle": cycle,
        "last_update": datetime.utcnow().isoformat(),
        "last_run": datetime.utcnow().isoformat()
    }
    redis_client.setex(key, 86400, json.dumps(data))


async def save_cycle_result(pool: asyncpg.Pool, tenant_id: str, run_id: str, cycle: int, result: dict):
    """Save cycle result to database"""
    query = """
        UPDATE bot_runs
        SET result_data = COALESCE(result_data, '{}'::jsonb) || $2::jsonb
        WHERE id = $1
    """
    async with pool.acquire() as conn:
        await conn.execute(query, UUID(run_id), json.dumps({f"cycle_{cycle}": result}))


async def log_error(pool: asyncpg.Pool, tenant_id: str, run_id: str, message: str):
    """Log error to database"""
    query = """
        INSERT INTO bot_logs (tenant_id, bot_run_id, level, message)
        VALUES ($1, $2, 'ERROR', $3)
    """
    async with pool.acquire() as conn:
        await conn.execute(query, UUID(tenant_id), UUID(run_id), message)


async def mark_run_completed(pool: asyncpg.Pool, run_id: str, cycles: int):
    """Mark run as completed"""
    query = """
        UPDATE bot_runs
        SET status = 'completed', completed_at = NOW(),
            result_data = COALESCE(result_data, '{}'::jsonb) || $2::jsonb
        WHERE id = $1
    """
    async with pool.acquire() as conn:
        await conn.execute(query, UUID(run_id), json.dumps({"total_cycles": cycles}))


async def mark_run_failed(pool: asyncpg.Pool, run_id: str, error: str):
    """Mark run as failed"""
    query = """
        UPDATE bot_runs
        SET status = 'failed', completed_at = NOW(), error_message = $2
        WHERE id = $1
    """
    async with pool.acquire() as conn:
        await conn.execute(query, UUID(run_id), error)


# Maintenance tasks
@app.task
def cleanup_expired_locks():
    """Clean up expired locks"""
    async def _cleanup():
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM bot_locks WHERE expires_at < NOW()"
            )
        await pool.close()
        return result
    
    return asyncio.run(_cleanup())


@app.task
def cleanup_old_logs():
    """Clean up logs older than 30 days"""
    async def _cleanup():
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM bot_logs WHERE created_at < NOW() - INTERVAL '30 days'"
            )
        await pool.close()
        return result
    
    return asyncio.run(_cleanup())
