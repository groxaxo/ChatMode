"""
User management routes (admin only).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from database import get_db
from models import User
from schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse
)
from auth import get_current_user, require_role, hash_password
from audit import log_action, compute_changes, get_client_ip, AuditAction
import crud

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def user_to_response(user: User) -> UserResponse:
    """Convert User model to response schema."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        enabled=user.enabled,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login
    )


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    List all users with pagination (admin only).
    
    - **role**: Filter by role (admin, moderator, viewer)
    - **enabled**: Filter by enabled status
    """
    users, total = crud.get_users(
        db,
        page=page,
        per_page=per_page,
        role=role,
        enabled=enabled
    )
    
    return UserListResponse(
        items=[user_to_response(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Create a new user (admin only)."""
    # Check for duplicate username
    existing = crud.get_user_by_username(db, user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "CONFLICT", "message": f"Username '{user_data.username}' already exists"}
        )
    
    # Check for duplicate email
    if user_data.email:
        existing_email = crud.get_user_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "CONFLICT", "message": f"Email '{user_data.email}' already registered"}
            )
    
    user = crud.create_user(db, user_data)
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.USER_CREATE,
        resource_type="user",
        resource_id=user.id,
        changes={"created": user_data.dict(exclude={"password"})},
        ip_address=get_client_ip(request)
    )
    
    return user_to_response(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get a user by ID (admin only)."""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "User not found"}
        )
    
    return user_to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Update a user (admin only)."""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "User not found"}
        )
    
    # Check for duplicate username if changing
    if user_data.username and user_data.username != user.username:
        existing = crud.get_user_by_username(db, user_data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "CONFLICT", "message": f"Username '{user_data.username}' already exists"}
            )
    
    # Check for duplicate email if changing
    if user_data.email and user_data.email != user.email:
        existing_email = crud.get_user_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "CONFLICT", "message": f"Email '{user_data.email}' already registered"}
            )
    
    # Compute changes for audit
    update_data = user_data.dict(exclude_unset=True)
    changes = compute_changes(user, update_data, [k for k in update_data.keys() if k != "password"])
    
    updated_user = crud.update_user(db, user_id, user_data)
    
    # Audit log
    if changes or user_data.password:
        if user_data.password:
            changes["password"] = "**changed**"
        
        log_action(
            db=db,
            user=current_user,
            action=AuditAction.USER_UPDATE,
            resource_type="user",
            resource_id=user_id,
            changes=changes,
            ip_address=get_client_ip(request)
        )
    
    return user_to_response(updated_user)


@router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Delete a user (admin only)."""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "User not found"}
        )
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_OPERATION", "message": "Cannot delete your own account"}
        )
    
    crud.delete_user(db, user_id)
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.USER_DELETE,
        resource_type="user",
        resource_id=user_id,
        changes={"deleted": True, "username": user.username},
        ip_address=get_client_ip(request)
    )
    
    return {"status": "deleted", "id": user_id}


@router.put("/{user_id}/enable")
async def enable_user(
    request: Request,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Enable a user account (admin only)."""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "User not found"}
        )
    
    user.enabled = True
    db.commit()
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.USER_ENABLE,
        resource_type="user",
        resource_id=user_id,
        ip_address=get_client_ip(request)
    )
    
    return {"status": "enabled", "id": user_id}


@router.put("/{user_id}/disable")
async def disable_user(
    request: Request,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Disable a user account (admin only)."""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "User not found"}
        )
    
    # Prevent self-disabling
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_OPERATION", "message": "Cannot disable your own account"}
        )
    
    user.enabled = False
    db.commit()
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.USER_DISABLE,
        resource_type="user",
        resource_id=user_id,
        ip_address=get_client_ip(request)
    )
    
    return {"status": "disabled", "id": user_id}


@router.put("/{user_id}/role")
async def change_user_role(
    request: Request,
    user_id: str,
    role: str = Query(..., regex="^(admin|moderator|viewer)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Change a user's role (admin only)."""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "User not found"}
        )
    
    old_role = user.role
    user.role = role
    db.commit()
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.USER_ROLE_CHANGE,
        resource_type="user",
        resource_id=user_id,
        changes={"role": {"old": old_role, "new": role}},
        ip_address=get_client_ip(request)
    )
    
    return {"status": "role_changed", "id": user_id, "old_role": old_role, "new_role": role}
