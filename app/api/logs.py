"""
Bot logs and history routes
"""
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.deps import get_current_user, CurrentUser
from ..models.schemas import (
    BotRunResponse, BotRunListResponse,
    BotLogResponse, BotLogListResponse
)
from ..db.database import get_pool

router = APIRouter(prefix="/bot", tags=["Bot Logs & History"])


@router.get("/runs", response_model=BotRunListResponse)
async def list_bot_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    triggered_by: Optional[str] = Query(None, description="Filter by trigger type"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List bot run history with pagination and filters.
    """
    pool = await get_pool()
    offset = (page - 1) * page_size
    
    # Build query
    where_clauses = ["tenant_id = $1"]
    params: List[Any] = [current_user.tenant_id]
    param_idx = 2
    
    if status_filter:
        where_clauses.append(f"status = ${param_idx}")
        params.append(status_filter)
        param_idx += 1
    
    if triggered_by:
        where_clauses.append(f"triggered_by = ${param_idx}")
        params.append(triggered_by)
        param_idx += 1
    
    where_sql = " AND ".join(where_clauses)
    
    async with pool.acquire() as conn:
        # Get total count
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM bot_runs WHERE {where_sql}",
            *params
        )
        
        # Get paginated results
        rows = await conn.fetch(
            f"""
            SELECT id, tenant_id, status, started_at, completed_at,
                   error_message, result_data, triggered_by
            FROM bot_runs
            WHERE {where_sql}
            ORDER BY started_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """,
            *params, page_size, offset
        )
    
    runs = [
        BotRunResponse(
            id=row['id'],
            tenant_id=row['tenant_id'],
            status=row['status'],
            started_at=row['started_at'],
            completed_at=row['completed_at'],
            error_message=row['error_message'],
            result_data=row['result_data'],
            triggered_by=row['triggered_by']
        )
        for row in rows
    ]
    
    return BotRunListResponse(
        runs=runs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/runs/{run_id}", response_model=BotRunResponse)
async def get_bot_run(
    run_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get details of a specific bot run.
    """
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, tenant_id, status, started_at, completed_at,
                   error_message, result_data, triggered_by
            FROM bot_runs
            WHERE id = $1 AND tenant_id = $2
            """,
            run_id, current_user.tenant_id
        )
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot run not found"
        )
    
    return BotRunResponse(
        id=row['id'],
        tenant_id=row['tenant_id'],
        status=row['status'],
        started_at=row['started_at'],
        completed_at=row['completed_at'],
        error_message=row['error_message'],
        result_data=row['result_data'],
        triggered_by=row['triggered_by']
    )


@router.get("/logs", response_model=BotLogListResponse)
async def list_bot_logs(
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, description="Filter by log level"),
    run_id: Optional[UUID] = Query(None, description="Filter by run ID"),
    since: Optional[datetime] = Query(None, description="Logs since this time"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List bot logs with filters.
    """
    pool = await get_pool()
    
    where_clauses = ["tenant_id = $1"]
    params: List[Any] = [current_user.tenant_id]
    param_idx = 2
    
    if level:
        where_clauses.append(f"level = ${param_idx}")
        params.append(level.upper())
        param_idx += 1
    
    if run_id:
        where_clauses.append(f"bot_run_id = ${param_idx}")
        params.append(run_id)
        param_idx += 1
    
    if since:
        where_clauses.append(f"created_at >= ${param_idx}")
        params.append(since)
        param_idx += 1
    
    where_sql = " AND ".join(where_clauses)
    
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM bot_logs WHERE {where_sql}",
            *params
        )
        
        rows = await conn.fetch(
            f"""
            SELECT id, level, message, metadata, created_at
            FROM bot_logs
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx}
            """,
            *params, limit
        )
    
    logs = [
        BotLogResponse(
            id=row['id'],
            level=row['level'],
            message=row['message'],
            metadata=row['metadata'],
            created_at=row['created_at']
        )
        for row in rows
    ]
    
    return BotLogListResponse(logs=logs, total=total)


@router.get("/logs/{run_id}", response_model=BotLogListResponse)
async def get_run_logs(
    run_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get all logs for a specific bot run.
    """
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        # Verify run belongs to tenant
        run_exists = await conn.fetchval(
            "SELECT 1 FROM bot_runs WHERE id = $1 AND tenant_id = $2",
            run_id, current_user.tenant_id
        )
        
        if not run_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot run not found"
            )
        
        rows = await conn.fetch(
            """
            SELECT id, level, message, metadata, created_at
            FROM bot_logs
            WHERE bot_run_id = $1 AND tenant_id = $2
            ORDER BY created_at ASC
            """,
            run_id, current_user.tenant_id
        )
    
    logs = [
        BotLogResponse(
            id=row['id'],
            level=row['level'],
            message=row['message'],
            metadata=row['metadata'],
            created_at=row['created_at']
        )
        for row in rows
    ]
    
    return BotLogListResponse(logs=logs, total=len(logs))


@router.delete("/logs", response_model=dict)
async def delete_old_logs(
    days: int = Query(30, ge=1, le=365, description="Delete logs older than X days"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete logs older than specified days.
    Only affects current tenant's logs.
    """
    pool = await get_pool()
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM bot_logs
            WHERE tenant_id = $1 AND created_at < $2
            """,
            current_user.tenant_id, cutoff
        )
        
        deleted_count = int(result.split()[-1])
    
    return {
        "deleted": deleted_count,
        "message": f"Deleted {deleted_count} logs older than {days} days"
    }
