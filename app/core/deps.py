"""
Dependency injection for FastAPI routes
"""
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from .config import settings
from .security import decode_access_token
from ..db.database import get_pool, BaseRepository
from ..models.schemas import TokenPayload, Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


class CurrentUser:
    """Current authenticated user context"""
    def __init__(
        self,
        user_id: UUID,
        email: str,
        tenant_id: UUID,
        role: str,
        is_superuser: bool = False
    ):
        self.id = user_id
        self.email = email
        self.tenant_id = tenant_id
        self.role = role
        self.is_superuser = is_superuser


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    x_tenant_id: Optional[str] = Header(None)
) -> CurrentUser:
    """
    Validate JWT token and return current user
    Optionally validates X-Tenant-ID header matches token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role = payload.get("role", "user")
        
        if user_id is None or tenant_id is None:
            raise credentials_exception
        
        # If X-Tenant-ID provided, must match token
        if x_tenant_id and x_tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant ID mismatch"
            )
        
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    # Fetch user from database to verify still active
    pool = await get_pool()
    query = """
        SELECT u.id, u.email, u.is_active, u.is_superuser
        FROM users u
        JOIN tenant_users tu ON u.id = tu.user_id
        WHERE u.id = $1 AND tu.tenant_id = $2 AND u.is_active = TRUE
    """
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, UUID(user_id), UUID(tenant_id))
    
    if not row:
        raise credentials_exception
    
    return CurrentUser(
        user_id=row['id'],
        email=row['email'],
        tenant_id=UUID(tenant_id),
        role=role,
        is_superuser=row['is_superuser']
    )


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Ensure user is active"""
    return current_user


def require_role(required_role: Role):
    """
    Dependency that requires a minimum role level
    Usage: Depends(require_role(Role.ADMIN))
    """
    role_hierarchy = {Role.VIEWER: 1, Role.USER: 2, Role.ADMIN: 3}
    
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        user_level = role_hierarchy.get(Role(current_user.role), 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' or higher required"
            )
        
        return current_user
    
    return role_checker


async def get_superuser(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Require superuser privileges"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    return current_user
