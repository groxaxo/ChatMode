"""
Audit log routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import math

from database import get_db
from models import User, AuditLog
from schemas import AuditLogResponse, AuditLogListResponse
from auth import get_current_user, require_role
import crud

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


def audit_log_to_response(log: AuditLog) -> AuditLogResponse:
    """Convert AuditLog model to response schema."""
    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        username=log.username,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        changes=log.changes,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        created_at=log.created_at
    )


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    days: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    List audit logs with filtering (admin only).
    
    - **user_id**: Filter by user who performed the action
    - **action**: Filter by action type (e.g., agent.create, user.login)
    - **resource_type**: Filter by resource type (agent, user, conversation, etc.)
    - **resource_id**: Filter by specific resource ID
    - **days**: Only show logs from the last N days
    """
    # Calculate date filter
    from_date = None
    if days:
        from_date = datetime.utcnow() - timedelta(days=days)
    
    logs, total = crud.get_audit_logs(
        db,
        page=page,
        per_page=per_page,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        from_date=from_date
    )
    
    return AuditLogListResponse(
        items=[audit_log_to_response(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get a single audit log entry (admin only)."""
    log = crud.get_audit_log(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Audit log not found"}
        )
    
    return audit_log_to_response(log)


@router.get("/resource/{resource_type}/{resource_id}", response_model=AuditLogListResponse)
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Get audit history for a specific resource (admin only).
    
    Shows all changes made to a particular resource.
    """
    logs, total = crud.get_audit_logs(
        db,
        page=page,
        per_page=per_page,
        resource_type=resource_type,
        resource_id=resource_id
    )
    
    return AuditLogListResponse(
        items=[audit_log_to_response(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1
    )


@router.get("/user/{user_id}/activity", response_model=AuditLogListResponse)
async def get_user_activity(
    user_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    days: Optional[int] = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Get activity history for a specific user (admin only).
    
    Shows all actions performed by a user.
    """
    from_date = None
    if days:
        from_date = datetime.utcnow() - timedelta(days=days)
    
    logs, total = crud.get_audit_logs(
        db,
        page=page,
        per_page=per_page,
        user_id=user_id,
        from_date=from_date
    )
    
    return AuditLogListResponse(
        items=[audit_log_to_response(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1
    )


@router.get("/stats/summary")
async def get_audit_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Get audit log statistics (admin only).
    
    Returns summary of actions over the specified period.
    """
    from_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all logs for the period
    logs, total = crud.get_audit_logs(
        db,
        page=1,
        per_page=10000,
        from_date=from_date
    )
    
    # Aggregate stats
    action_counts = {}
    resource_counts = {}
    user_counts = {}
    daily_counts = {}
    
    for log in logs:
        # Count by action
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
        
        # Count by resource type
        if log.resource_type:
            resource_counts[log.resource_type] = resource_counts.get(log.resource_type, 0) + 1
        
        # Count by user
        if log.username:
            user_counts[log.username] = user_counts.get(log.username, 0) + 1
        
        # Count by day
        day_key = log.created_at.strftime("%Y-%m-%d")
        daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
    
    return {
        "period_days": days,
        "total_actions": total,
        "by_action": action_counts,
        "by_resource_type": resource_counts,
        "by_user": dict(sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        "daily_activity": daily_counts
    }
