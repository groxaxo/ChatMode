"""
Environment configuration management routes.
"""

import asyncio
import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..audit import AuditAction, get_client_ip, log_action
from ..auth import require_role
from ..database import get_db
from ..models import User
from ..state_sync import get_project_root
from ..services.provider_init import discover_providers_from_shell_configs, initialize_providers

logger = logging.getLogger(__name__)

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


@router.post("/env/import-shell", tags=["config"])
async def import_shell_env(
    request: Request,
    background_refresh: bool = True,
    current_user: User = Depends(require_role(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    """Merge API keys from shell configs into the .env file and reinitialise providers."""
    # Scan shell config files for API keys and base URLs
    providers, scanned_files = discover_providers_from_shell_configs()
    
    # Build a dict of env vars to write
    shell_vars = {}
    for p in providers:
        provider_name = p.get("name")
        if not provider_name:
            # Skip providers without names
            continue
            
        # Map to expected env variable names (e.g. DEEPSEEK_API_KEY)
        if p.get("api_key"):
            env_key = provider_name.upper() + "_API_KEY"
            shell_vars[env_key] = p["api_key"]
        if p.get("base_url"):
            env_url = provider_name.upper() + "_BASE_URL"
            shell_vars[env_url] = p["base_url"]
    
    # Read existing .env
    env_path = Path(os.getenv("ENV_FILE", get_project_root() + "/.env"))
    existing = ""
    if env_path.exists():
        existing = env_path.read_text()
    
    # Update or append values
    lines = existing.splitlines() if existing else []
    # Remove any existing lines for these keys (check at start of line)
    lines = [line for line in lines if not any(line.strip().startswith(k+"=") for k in shell_vars.keys())]
    # Append new variables
    for key, value in shell_vars.items():
        lines.append(f"{key}={value}")
    env_content = "\n".join(lines) + "\n"
    
    # Write back to .env
    env_path.write_text(env_content)
    
    # Reinitialise providers and sync models using the injected db session
    try:
        # scan_shell_configs=False because we already merged shell variables
        result = await initialize_providers(db, auto_sync=True, scan_shell_configs=False)
    except Exception as e:
        # Log error but don't fail the request
        logger.error(f"Failed to initialize providers after shell import: {e}")
        result = {"providers": [], "total_discovered": 0, "successful": 0, "failed": 0}
    
    # Log the action
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AGENT_UPDATE,
        resource_type="env_config",
        resource_id=".env",
        changes={"action": "import_shell", "scanned_files": scanned_files},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    
    # Return updated env content for display
    updated_content = env_path.read_text()
    
    return {
        "status": "imported",
        "scanned_files": scanned_files,
        "providers": result["providers"],
        "content": updated_content
    }
