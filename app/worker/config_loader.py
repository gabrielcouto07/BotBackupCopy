"""
Configuration loader for tenant-specific settings
"""
import os
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import asyncpg

from ..core.config import settings


class TenantConfigLoader:
    """Loads and decrypts tenant-specific configurations from database"""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize config loader.
        
        Args:
            pool: Database connection pool
        """
        self.pool = pool
        
        # Initialize encryption
        encryption_key = settings.CONFIG_ENCRYPTION_KEY
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        else:
            self.cipher = None
    
    async def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        """
        Load all configurations for a tenant.
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            Dictionary of configuration key-value pairs
        """
        query = """
            SELECT config_key, config_value, is_encrypted
            FROM bot_configs
            WHERE tenant_id = $1
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, tenant_id)
        
        config = {}
        for row in rows:
            key = row['config_key']
            value = row['config_value']
            
            # Decrypt if encrypted
            if row['is_encrypted'] and self.cipher:
                try:
                    value = self.cipher.decrypt(value.encode()).decode()
                except Exception:
                    # Keep encrypted value if decryption fails
                    pass
            
            # Type conversion
            if value.lower() in ('true', 'false'):
                config[key] = value.lower() == 'true'
            elif value.isdigit():
                config[key] = int(value)
            else:
                config[key] = value
        
        return config
    
    async def get_tenant_secrets(self, tenant_id: str) -> Dict[str, str]:
        """
        Load encrypted secrets for a tenant.
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            Dictionary of decrypted secret key-value pairs
        """
        if not self.cipher:
            return {}
        
        query = """
            SELECT secret_key, encrypted_value
            FROM tenant_secrets
            WHERE tenant_id = $1
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, tenant_id)
        
        secrets = {}
        for row in rows:
            try:
                decrypted = self.cipher.decrypt(bytes(row['encrypted_value']))
                secrets[row['secret_key']] = decrypted.decode()
            except Exception:
                # Skip if decryption fails
                pass
        
        return secrets
    
    async def get_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant metadata.
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            Tenant info dict or None
        """
        query = """
            SELECT id, name, slug, subscription_tier, is_active, max_workers
            FROM tenants
            WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, tenant_id)
        
        if not row:
            return None
        
        return {
            'id': str(row['id']),
            'name': row['name'],
            'slug': row['slug'],
            'subscription_tier': row['subscription_tier'],
            'is_active': row['is_active'],
            'max_workers': row['max_workers']
        }
    
    async def is_tenant_active(self, tenant_id: str) -> bool:
        """
        Check if tenant is active.
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            True if tenant is active
        """
        query = "SELECT is_active FROM tenants WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            is_active = await conn.fetchval(query, tenant_id)
        
        return is_active is True


class ConfigCache:
    """Redis-based configuration cache"""
    
    def __init__(self, redis_client, ttl: int = 300):
        """
        Initialize config cache.
        
        Args:
            redis_client: Redis client instance
            ttl: Cache TTL in seconds (default 5 minutes)
        """
        self.redis = redis_client
        self.ttl = ttl
    
    async def get_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get cached config for tenant."""
        import json
        key = f"config:{tenant_id}"
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    async def set_config(self, tenant_id: str, config: Dict[str, Any]):
        """Cache config for tenant."""
        import json
        key = f"config:{tenant_id}"
        await self.redis.setex(key, self.ttl, json.dumps(config))
    
    async def invalidate(self, tenant_id: str):
        """Invalidate cached config for tenant."""
        key = f"config:{tenant_id}"
        await self.redis.delete(key)
