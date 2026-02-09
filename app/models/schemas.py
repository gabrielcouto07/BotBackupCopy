"""
Pydantic schemas for API requests and responses
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================
# ENUMS
# ============================================

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class BotStatusEnum(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LogLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


# ============================================
# AUTH SCHEMAS
# ============================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: UUID
    expires_at: datetime


class TokenPayload(BaseModel):
    sub: str  # user_id
    tenant_id: str
    exp: datetime
    role: str


# ============================================
# TENANT SCHEMAS
# ============================================

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = None  # Auto-generated if not provided


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    subscription_tier: str
    is_active: bool
    max_workers: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantUserResponse(BaseModel):
    user: UserResponse
    role: str
    created_at: datetime


# ============================================
# BOT CONFIG SCHEMAS
# ============================================

class BotConfigUpdate(BaseModel):
    # Facebook/Amazon credentials
    platform_email: Optional[str] = None
    platform_password: Optional[str] = None
    
    # Bot settings
    check_interval_minutes: Optional[int] = Field(default=15, ge=5, le=60)
    max_retries: Optional[int] = Field(default=3, ge=1, le=10)
    headless: Optional[bool] = True
    
    # Notification settings
    webhook_url: Optional[str] = None
    notify_on_error: Optional[bool] = True
    
    # Custom settings (for flexibility)
    custom_settings: Optional[Dict[str, Any]] = None


class BotConfigResponse(BaseModel):
    platform_email: Optional[str] = None
    check_interval_minutes: int = 15
    max_retries: int = 3
    headless: bool = True
    webhook_url: Optional[str] = None
    notify_on_error: bool = True
    custom_settings: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None


# ============================================
# BOT STATUS & CONTROL SCHEMAS
# ============================================

class BotStatus(BaseModel):
    tenant_id: UUID
    status: BotStatusEnum
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    current_cycle: Optional[int] = None
    uptime_seconds: Optional[float] = None


class BotStartResponse(BaseModel):
    status: str = "started"
    run_id: UUID
    message: str = "Bot started successfully"


class BotStopResponse(BaseModel):
    status: str = "stopped"
    message: str = "Stop command sent to bot"


class TestRunRequest(BaseModel):
    dry_run: bool = True  # Don't execute actions, just test
    timeout_seconds: int = Field(default=300, ge=30, le=600)


class TestRunResponse(BaseModel):
    run_id: UUID
    status: str
    duration_seconds: float
    orders_found: int
    actions_taken: int
    errors: List[str]


# ============================================
# BOT RUN SCHEMAS
# ============================================

class BotRunResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    triggered_by: str

    model_config = ConfigDict(from_attributes=True)


class BotRunListResponse(BaseModel):
    runs: List[BotRunResponse]
    total: int
    page: int
    page_size: int


# ============================================
# BOT LOG SCHEMAS
# ============================================

class BotLogResponse(BaseModel):
    id: UUID
    level: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BotLogListResponse(BaseModel):
    logs: List[BotLogResponse]
    total: int


# ============================================
# HEALTH & METRICS SCHEMAS
# ============================================

class HealthCheckResponse(BaseModel):
    status: str
    database: str
    redis: str
    version: str = "1.0.0"


class MetricsResponse(BaseModel):
    active_bots: int
    pending_tasks: int
    total_runs_today: int
    total_tenants: int
    total_users: int


# ============================================
# REGISTRATION SCHEMAS
# ============================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    tenant_name: str = Field(..., min_length=2, max_length=255)


class RegisterResponse(BaseModel):
    user: UserResponse
    tenant: TenantResponse
    token: Token


# ============================================
# GENERIC RESPONSE SCHEMAS
# ============================================

class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
