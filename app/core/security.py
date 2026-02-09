"""
Security utilities: JWT tokens, password hashing
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import jwt
from passlib.context import CryptContext

from .config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> tuple[str, datetime]:
    """
    Create JWT access token with tenant context
    Returns: (token, expiration_datetime)
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt, expire


def decode_access_token(token: str) -> dict:
    """
    Decode and validate JWT token
    Raises: jwt.InvalidTokenError if invalid
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    return payload


def create_refresh_token(user_id: UUID) -> str:
    """Create a longer-lived refresh token"""
    expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire
    }
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
