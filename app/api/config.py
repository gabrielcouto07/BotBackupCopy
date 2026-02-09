"""
Bot configuration routes: get/update bot settings
"""
from datetime import datetime
from uuid import UUID
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.config import settings
from ..core.deps import get_current_user, require_role, CurrentUser
from ..core.crypto import get_crypto
from ..models.schemas import BotConfigUpdate, BotConfigResponse, Role, MessageResponse
from ..db.database import get_pool

router = APIRouter(prefix="/bot/config", tags=["Bot Configuration"])


@router.get("", response_model=BotConfigResponse)
async def get_bot_config(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get bot configuration for current tenant.
    Passwords are masked.
    """
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT config_key, config_value, is_encrypted, updated_at
            FROM bot_configs
            WHERE tenant_id = $1
            """,
            current_user.tenant_id
        )
    
    config = {}
    latest_update = None
    
    for row in rows:
        key = row['config_key']
        value = row['config_value']
        
        # Don't decrypt passwords for display, just show masked
        if row['is_encrypted']:
            config[key] = "********"
        elif value.lower() in ('true', 'false'):
            config[key] = value.lower() == 'true'
        elif value.isdigit():
            config[key] = int(value)
        else:
            config[key] = value
        
        if row['updated_at']:
            if latest_update is None or row['updated_at'] > latest_update:
                latest_update = row['updated_at']
    
    return BotConfigResponse(
        platform_email=config.get('platform_email'),
        check_interval_minutes=config.get('check_interval_minutes', 15),
        max_retries=config.get('max_retries', 3),
        headless=config.get('headless', True),
        webhook_url=config.get('webhook_url'),
        notify_on_error=config.get('notify_on_error', True),
        custom_settings=config.get('custom_settings'),
        updated_at=latest_update
    )


@router.put("", response_model=BotConfigResponse)
async def update_bot_config(
    config: BotConfigUpdate,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """
    Update bot configuration.
    Requires ADMIN role.
    Sensitive fields are encrypted.
    """
    pool = await get_pool()
    crypto = get_crypto()
    
    # Build updates from provided fields
    updates: Dict[str, tuple[str, bool]] = {}  # key -> (value, is_encrypted)
    
    if config.platform_email is not None:
        updates['platform_email'] = (config.platform_email, False)
    
    if config.platform_password is not None:
        # Encrypt password
        encrypted = crypto.encrypt(config.platform_password)
        updates['platform_password'] = (encrypted, True)
    
    if config.check_interval_minutes is not None:
        updates['check_interval_minutes'] = (str(config.check_interval_minutes), False)
    
    if config.max_retries is not None:
        updates['max_retries'] = (str(config.max_retries), False)
    
    if config.headless is not None:
        updates['headless'] = (str(config.headless).lower(), False)
    
    if config.webhook_url is not None:
        updates['webhook_url'] = (config.webhook_url, False)
    
    if config.notify_on_error is not None:
        updates['notify_on_error'] = (str(config.notify_on_error).lower(), False)
    
    if config.custom_settings is not None:
        import json
        updates['custom_settings'] = (json.dumps(config.custom_settings), False)
    
    async with pool.acquire() as conn:
        for key, (value, is_encrypted) in updates.items():
            await conn.execute(
                """
                INSERT INTO bot_configs (tenant_id, config_key, config_value, is_encrypted, updated_by, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (tenant_id, config_key)
                DO UPDATE SET config_value = $3, is_encrypted = $4, updated_by = $5, updated_at = NOW()
                """,
                current_user.tenant_id, key, value, is_encrypted, current_user.id
            )
        
        # Log the change
        await conn.execute(
            """
            INSERT INTO audit_logs (tenant_id, user_id, action, changes)
            VALUES ($1, $2, 'config.update', $3)
            """,
            current_user.tenant_id,
            current_user.id,
            {"updated_keys": list(updates.keys())}
        )
    
    # Notify running bot to reload config
    try:
        import redis.asyncio as redis_lib
        redis_client = redis_lib.from_url(settings.REDIS_URL)
        tenant_id = str(current_user.tenant_id)
        await redis_client.publish(f"bot_commands:{tenant_id}", "reload_config")
        await redis_client.close()
    except Exception:
        pass  # Redis not available, bot will get new config on next cycle
    
    # Return updated config
    return await get_bot_config(current_user)


@router.delete("/{config_key}", response_model=MessageResponse)
async def delete_config_key(
    config_key: str,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """
    Delete a specific configuration key.
    """
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM bot_configs
            WHERE tenant_id = $1 AND config_key = $2
            """,
            current_user.tenant_id, config_key
        )
    
    return MessageResponse(
        message=f"Config key '{config_key}' deleted",
        success=True
    )


@router.post("/reset", response_model=MessageResponse)
async def reset_to_defaults(
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """
    Reset all configurations to default values.
    """
    pool = await get_pool()
    
    default_configs = [
        ("check_interval_minutes", "15", False),
        ("max_retries", "3", False),
        ("headless", "true", False),
        ("notify_on_error", "true", False),
    ]
    
    async with pool.acquire() as conn:
        # Delete all existing configs
        await conn.execute(
            "DELETE FROM bot_configs WHERE tenant_id = $1",
            current_user.tenant_id
        )
        
        # Insert defaults
        for key, value, encrypted in default_configs:
            await conn.execute(
                """
                INSERT INTO bot_configs (tenant_id, config_key, config_value, is_encrypted, updated_by)
                VALUES ($1, $2, $3, $4, $5)
                """,
                current_user.tenant_id, key, value, encrypted, current_user.id
            )
        
        # Log the reset
        await conn.execute(
            """
            INSERT INTO audit_logs (tenant_id, user_id, action)
            VALUES ($1, $2, 'config.reset')
            """,
            current_user.tenant_id, current_user.id
        )
    
    return MessageResponse(
        message="Configuration reset to defaults",
        success=True
    )
