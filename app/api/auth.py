"""
Authentication routes: register, login, user management
"""
from datetime import datetime
from uuid import UUID
import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..core.security import verify_password, get_password_hash, create_access_token
from ..core.deps import get_current_user, CurrentUser
from ..db.database import get_pool
from ..models.schemas import (
    UserCreate, UserResponse, Token, RegisterRequest, RegisterResponse,
    TenantResponse, MessageResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def generate_slug(name: str) -> str:
    """Generate URL-safe slug from name"""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug[:100]


@router.post("/register", response_model=RegisterResponse)
async def register(data: RegisterRequest):
    """
    Register a new user and create their tenant
    """
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        # Check if email already exists
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            data.email.lower()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Generate unique slug
        base_slug = generate_slug(data.tenant_name)
        slug = base_slug
        counter = 1
        
        while True:
            existing_slug = await conn.fetchrow(
                "SELECT id FROM tenants WHERE slug = $1", slug
            )
            if not existing_slug:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create tenant
        tenant_row = await conn.fetchrow(
            """
            INSERT INTO tenants (name, slug, subscription_tier, is_active, max_workers)
            VALUES ($1, $2, 'free', TRUE, 1)
            RETURNING id, name, slug, subscription_tier, is_active, max_workers, created_at
            """,
            data.tenant_name, slug
        )
        
        # Create user
        hashed_password = get_password_hash(data.password)
        user_row = await conn.fetchrow(
            """
            INSERT INTO users (email, hashed_password, full_name, is_active)
            VALUES ($1, $2, $3, TRUE)
            RETURNING id, email, full_name, is_active, created_at
            """,
            data.email.lower(), hashed_password, data.full_name
        )
        
        # Create tenant_user relationship with admin role
        await conn.execute(
            """
            INSERT INTO tenant_users (tenant_id, user_id, role)
            VALUES ($1, $2, 'admin')
            """,
            tenant_row['id'], user_row['id']
        )
        
        # Create default bot configs
        default_configs = [
            ("check_interval_minutes", "15", False),
            ("max_retries", "3", False),
            ("headless", "true", False),
            ("notify_on_error", "true", False),
        ]
        
        for key, value, encrypted in default_configs:
            await conn.execute(
                """
                INSERT INTO bot_configs (tenant_id, config_key, config_value, is_encrypted)
                VALUES ($1, $2, $3, $4)
                """,
                tenant_row['id'], key, value, encrypted
            )
    
    # Create access token
    access_token, expires_at = create_access_token(
        user_id=user_row['id'],
        tenant_id=tenant_row['id'],
        role="admin"
    )
    
    return RegisterResponse(
        user=UserResponse(
            id=user_row['id'],
            email=user_row['email'],
            full_name=user_row['full_name'],
            is_active=user_row['is_active'],
            created_at=user_row['created_at']
        ),
        tenant=TenantResponse(
            id=tenant_row['id'],
            name=tenant_row['name'],
            slug=tenant_row['slug'],
            subscription_tier=tenant_row['subscription_tier'],
            is_active=tenant_row['is_active'],
            max_workers=tenant_row['max_workers'],
            created_at=tenant_row['created_at']
        ),
        token=Token(
            access_token=access_token,
            token_type="bearer",
            tenant_id=tenant_row['id'],
            expires_at=expires_at
        )
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with email and password, receive JWT token
    """
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        # Get user with tenant info
        row = await conn.fetchrow(
            """
            SELECT u.id, u.email, u.hashed_password, u.is_active,
                   tu.tenant_id, tu.role
            FROM users u
            JOIN tenant_users tu ON u.id = tu.user_id
            WHERE u.email = $1
            LIMIT 1
            """,
            form_data.username.lower()  # username is email
        )
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not row['is_active']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    if not verify_password(form_data.password, row['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token, expires_at = create_access_token(
        user_id=row['id'],
        tenant_id=row['tenant_id'],
        role=row['role']
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        tenant_id=row['tenant_id'],
        expires_at=expires_at
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current authenticated user info"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, full_name, is_active, created_at
            FROM users WHERE id = $1
            """,
            current_user.id
        )
    
    return UserResponse(
        id=row['id'],
        email=row['email'],
        full_name=row['full_name'],
        is_active=row['is_active'],
        created_at=row['created_at']
    )


@router.post("/switch-tenant/{tenant_id}", response_model=Token)
async def switch_tenant(
    tenant_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Switch to a different tenant (for users in multiple tenants)
    """
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        # Check if user belongs to the target tenant
        row = await conn.fetchrow(
            """
            SELECT role FROM tenant_users
            WHERE user_id = $1 AND tenant_id = $2
            """,
            current_user.id, tenant_id
        )
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this tenant"
        )
    
    access_token, expires_at = create_access_token(
        user_id=current_user.id,
        tenant_id=tenant_id,
        role=row['role']
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        tenant_id=tenant_id,
        expires_at=expires_at
    )


@router.get("/tenants", response_model=list[TenantResponse])
async def list_user_tenants(
    current_user: CurrentUser = Depends(get_current_user)
):
    """List all tenants the current user belongs to"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT t.id, t.name, t.slug, t.subscription_tier, 
                   t.is_active, t.max_workers, t.created_at
            FROM tenants t
            JOIN tenant_users tu ON t.id = tu.tenant_id
            WHERE tu.user_id = $1 AND t.is_active = TRUE
            ORDER BY t.name
            """,
            current_user.id
        )
    
    return [
        TenantResponse(
            id=row['id'],
            name=row['name'],
            slug=row['slug'],
            subscription_tier=row['subscription_tier'],
            is_active=row['is_active'],
            max_workers=row['max_workers'],
            created_at=row['created_at']
        )
        for row in rows
    ]
