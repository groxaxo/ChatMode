"""
Authentication routes.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import TokenRequest, TokenResponse, ErrorResponse
from ..auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from ..audit import log_action, get_client_ip, AuditAction

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse, responses={401: {"model": ErrorResponse}})
async def login(
    request: Request,
    credentials: TokenRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    """
    user = authenticate_user(db, credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Incorrect username or password"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Log successful login
    log_action(
        db=db,
        user=user,
        action=AuditAction.USER_LOGIN,
        resource_type="user",
        resource_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Logout (invalidate token on client side).
    
    Note: With JWT, tokens are stateless. This endpoint is for audit logging.
    For real invalidation, implement a token blacklist.
    """
    from ..auth import get_current_user_optional
    from fastapi.security import HTTPBearer
    
    security = HTTPBearer(auto_error=False)
    credentials = await security(request)
    
    if credentials:
        user = await get_current_user_optional(request, credentials, db)
        if user:
            log_action(
                db=db,
                user=user,
                action=AuditAction.USER_LOGOUT,
                resource_type="user",
                resource_id=user.id,
                ip_address=get_client_ip(request)
            )
    
    return {"status": "logged_out"}


@router.get("/me")
async def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user info.
    """
    from ..auth import get_current_user
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    
    security = HTTPBearer()
    credentials: HTTPAuthorizationCredentials = await security(request)
    user = await get_current_user(request, credentials, db)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None
    }
