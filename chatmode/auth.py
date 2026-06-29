"""
Authentication and authorization utilities.
"""

import base64
import hashlib
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, UserRole

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta=None) -> str:
    """Create a JWT access token."""
    from datetime import timedelta

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.enabled:
        return None

    user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    return user


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.

    Raises HTTPException if not authenticated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "UNAUTHORIZED",
            "message": "Invalid authentication credentials",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "User account is disabled"},
        )

    return user


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise None.

    Useful for endpoints that work with or without authentication.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


def require_role(allowed_roles: list):
    """
    Dependency factory for role-based access control.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user = Depends(require_role(["admin"]))):
            pass
    """

    async def role_checker(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db),
    ) -> User:
        user = await get_current_user(request, credentials, db)

        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": f"Insufficient permissions. Required role: {', '.join(allowed_roles)}",
                },
            )

        return user

    return role_checker


def create_initial_admin(
    db: Session, username: str = "admin", password: Optional[str] = None
):
    """
    Create initial admin user if no users exist.

    Should be called during first-time setup. If no password is provided,
    a secure random password is generated and printed once.
    """
    existing = db.query(User).first()
    if existing:
        return None

    generated = password is None
    if generated:
        password = secrets.token_urlsafe(16)

    admin = User(
        username=username,
        password_hash=hash_password(password),
        role=UserRole.ADMIN.value,
        enabled=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    if generated:
        print(f"Created initial admin user: {username}")
        print(f"Generated password (save this, it will not be shown again): {password}")
    else:
        print(f"Created initial admin user: {username}")
    return admin


# ============================================================================
# API key encryption using Fernet symmetric encryption
# ============================================================================

def _get_fernet():
    """Derive a Fernet cipher from SECRET_KEY."""
    from cryptography.fernet import Fernet

    key_bytes = hashlib.sha256(SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for storage using Fernet symmetric encryption."""
    if not api_key:
        return ""
    return _get_fernet().encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key from storage. Falls back to legacy base64 for old records."""
    if not encrypted_key:
        return ""
    from cryptography.fernet import InvalidToken

    try:
        return _get_fernet().decrypt(encrypted_key.encode()).decode()
    except (InvalidToken, Exception):
        # Legacy base64-encoded keys (pre-encryption migration)
        try:
            return base64.b64decode(encrypted_key.encode()).decode()
        except Exception:
            logger.warning("Failed to decrypt API key — key may need to be re-entered")
            return ""
