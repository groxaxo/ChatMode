"""
Environment configuration management routes.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..audit import AuditAction, get_client_ip, log_action
from ..auth import require_role
from ..database import get_db
from ..models import User
from ..state_sync import get_project_root

router = APIRouter(prefix="/api/v1/config", tags=["config"])


class EnvConfigUpdate(BaseModel):
    content: str


@router.get("/env")
async def get_env_config(
    request: Request,
    current_user: User = Depends(require_role(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    """Read the .env configuration file contents."""
    env_path = os.path.join(get_project_root(), ".env")
    if not os.path.exists(env_path):
        raise HTTPException(status_code=404, detail=".env file not found")

    with open(env_path, "r") as f:
        content = f.read()

    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AGENT_READ,
        resource_type="env_config",
        resource_id=".env",
        changes={"action": "read"},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {"path": env_path, "content": content}


@router.put("/env", status_code=status.HTTP_200_OK)
async def update_env_config(
    request: Request,
    payload: EnvConfigUpdate,
    current_user: User = Depends(require_role(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    """Overwrite the .env configuration file contents."""
    env_path = os.path.join(get_project_root(), ".env")
    os.makedirs(os.path.dirname(env_path), exist_ok=True)

    with open(env_path, "w") as f:
        f.write(payload.content)

    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AGENT_UPDATE,
        resource_type="env_config",
        resource_id=".env",
        changes={"action": "write"},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {"status": "saved", "path": env_path}
