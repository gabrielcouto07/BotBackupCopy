"""
Database connection and session management for multi-tenant SaaS
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncpg
from asyncpg.pool import Pool

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/bot_saas"
)

# Connection pool global
_pool: Pool | None = None


async def create_pool() -> Pool:
    """Create database connection pool"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60,
        )
    return _pool


async def close_pool():
    """Close database connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_pool() -> Pool:
    """Get database pool, creating if necessary"""
    if _pool is None:
        await create_pool()
    return _pool


@asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection from pool"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


async def init_db():
    """Initialize database with schema"""
    import os
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    
    async with get_connection() as conn:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        await conn.execute(schema_sql)


# Repository helpers
class BaseRepository:
    """Base repository with tenant isolation"""
    
    def __init__(self, pool: Pool):
        self.pool = pool
    
    async def fetch_one(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetch_all(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch_val(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
