"""
Provider Management API Routes.

Provides endpoints for:
- CRUD operations on providers
- Syncing models from providers
- Listing available models
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Provider, ProviderModel, User
from ..services.provider_sync import (
    create_provider_from_config,
    detect_provider_type,
    fetch_models_from_provider,
    get_all_available_models,
    sync_all_providers,
    sync_provider_models,
)

router = APIRouter(prefix="/api/v1/providers", tags=["providers"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class ProviderCreate(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Unique provider name"
    )
    display_name: Optional[str] = Field(None, max_length=200)
    base_url: str = Field(..., max_length=500, description="Provider API base URL")
    api_key: Optional[str] = Field(
        None, max_length=500, description="API key (optional)"
    )
    provider_type: Optional[str] = Field(
        None, max_length=50, description="Provider type (auto-detected if not provided)"
    )
    auto_sync_enabled: bool = Field(True, description="Enable automatic model syncing")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)


class ProviderUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=200)
    base_url: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)
    provider_type: Optional[str] = Field(None, max_length=50)
    auto_sync_enabled: Optional[bool] = None
    enabled: Optional[bool] = None
    headers: Optional[Dict[str, str]] = None


class ProviderModelResponse(BaseModel):
    id: str
    model_id: str
    display_name: Optional[str]
    supports_tools: bool
    supports_vision: bool
    context_window: Optional[int]
    enabled: bool
    is_default: bool

    model_config = ConfigDict(from_attributes=True)


class ProviderResponse(BaseModel):
    id: str
    name: str
    display_name: Optional[str]
    provider_type: str
    base_url: str
    auto_sync_enabled: bool
    last_sync_at: Optional[str]
    sync_status: str
    sync_error: Optional[str]
    enabled: bool
    is_default: bool
    model_count: int

    model_config = ConfigDict(from_attributes=True)


class ProviderListResponse(BaseModel):
    providers: List[ProviderResponse]
    total: int


class ProviderDetailResponse(ProviderResponse):
    models: List[ProviderModelResponse]


class SyncResult(BaseModel):
    success: bool
    provider_id: str
    provider_name: str
    added: int = 0
    updated: int = 0
    removed: int = 0
    total_models: int = 0
    error: Optional[str] = None


class SyncAllResult(BaseModel):
    results: List[SyncResult]
    total_providers: int
    successful: int
    failed: int


class ModelDiscoveryResponse(BaseModel):
    provider_type: str
    display_name: str
    models: List[Dict[str, Any]]
    count: int


class ProviderTestRequest(BaseModel):
    base_url: str
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


class ProviderTestResponse(BaseModel):
    success: bool
    provider_type: str
    display_name: str
    models_found: int
    error: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================


def _provider_to_response(provider: Provider, db: Session) -> ProviderResponse:
    """Convert Provider model to response schema."""
    model_count = (
        db.query(ProviderModel).filter(ProviderModel.provider_id == provider.id).count()
    )

    return ProviderResponse(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        provider_type=provider.provider_type,
        base_url=provider.base_url,
        auto_sync_enabled=provider.auto_sync_enabled,
        last_sync_at=(
            provider.last_sync_at.isoformat() if provider.last_sync_at else None
        ),
        sync_status=provider.sync_status,
        sync_error=provider.sync_error,
        enabled=provider.enabled,
        is_default=provider.is_default,
        model_count=model_count,
    )


def _model_to_response(model: ProviderModel) -> ProviderModelResponse:
    """Convert ProviderModel to response schema."""
    return ProviderModelResponse(
        id=model.id,
        model_id=model.model_id,
        display_name=model.display_name,
        supports_tools=model.supports_tools,
        supports_vision=model.supports_vision,
        context_window=model.context_window,
        enabled=model.enabled,
        is_default=model.is_default,
    )


# =============================================================================
# API Routes
# =============================================================================


@router.get("/", response_model=ProviderListResponse)
async def list_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_disabled: bool = False,
):
    """List all providers."""
    query = db.query(Provider)
    if not include_disabled:
        query = query.filter(Provider.enabled == True)

    providers = query.all()

    return ProviderListResponse(
        providers=[_provider_to_response(p, db) for p in providers],
        total=len(providers),
    )


@router.post("/", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: ProviderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new provider."""
    # Check if provider name already exists
    existing = db.query(Provider).filter(Provider.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Provider with name '{data.name}' already exists",
        )

    # Auto-detect provider type if not provided
    provider_type = data.provider_type
    if not provider_type:
        provider_type = detect_provider_type(data.base_url)

    # Create provider
    provider = create_provider_from_config(
        db=db,
        name=data.name,
        base_url=data.base_url,
        api_key=data.api_key,
        provider_type=provider_type,
        auto_sync=data.auto_sync_enabled,
    )

    if data.display_name:
        provider.display_name = data.display_name

    if data.headers:
        provider.headers = data.headers

    db.commit()
    db.refresh(provider)

    return _provider_to_response(provider, db)


@router.get("/{provider_id}", response_model=ProviderDetailResponse)
async def get_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get provider details with models."""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    models = (
        db.query(ProviderModel).filter(ProviderModel.provider_id == provider_id).all()
    )

    response = _provider_to_response(provider, db)
    return ProviderDetailResponse(
        **response.model_dump(), models=[_model_to_response(m) for m in models]
    )


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str,
    data: ProviderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update provider configuration."""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    # Update fields
    if data.display_name is not None:
        provider.display_name = data.display_name
    if data.base_url is not None:
        provider.base_url = data.base_url
        # Re-detect provider type if URL changed
        provider.provider_type = detect_provider_type(data.base_url)
    if data.api_key is not None:
        provider.api_key_encrypted = data.api_key
    if data.provider_type is not None:
        provider.provider_type = data.provider_type
    if data.auto_sync_enabled is not None:
        provider.auto_sync_enabled = data.auto_sync_enabled
    if data.enabled is not None:
        provider.enabled = data.enabled
    if data.headers is not None:
        provider.headers = data.headers

    db.commit()
    db.refresh(provider)

    return _provider_to_response(provider, db)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a provider and all its models."""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    db.delete(provider)
    db.commit()

    return None


@router.post("/{provider_id}/sync", response_model=SyncResult)
async def sync_provider(
    provider_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync models from a provider."""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    result = await sync_provider_models(db, provider)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=result["error"]
        )

    return SyncResult(**result)


@router.post("/sync-all", response_model=SyncAllResult)
async def sync_all(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync models from all enabled providers."""
    results = await sync_all_providers(db)

    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    return SyncAllResult(
        results=[SyncResult(**r) for r in results],
        total_providers=len(results),
        successful=successful,
        failed=failed,
    )


@router.get("/{provider_id}/models", response_model=List[ProviderModelResponse])
async def list_provider_models(
    provider_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_disabled: bool = False,
):
    """List all models for a provider."""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    query = db.query(ProviderModel).filter(ProviderModel.provider_id == provider_id)
    if not include_disabled:
        query = query.filter(ProviderModel.enabled == True)

    models = query.all()
    return [_model_to_response(m) for m in models]


@router.put("/{provider_id}/models/{model_id}/enable")
async def enable_model(
    provider_id: str,
    model_id: str,
    enabled: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable or disable a specific model."""
    model = (
        db.query(ProviderModel)
        .filter(ProviderModel.provider_id == provider_id, ProviderModel.id == model_id)
        .first()
    )

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )

    model.enabled = enabled
    db.commit()

    return {"success": True, "model_id": model_id, "enabled": enabled}


@router.post("/test", response_model=ProviderTestResponse)
async def test_provider(
    data: ProviderTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test a provider connection and discover models without saving."""
    try:
        # Detect provider type
        provider_type = detect_provider_type(data.base_url)
        from ..services.provider_sync import get_provider_display_name

        display_name = get_provider_display_name(provider_type, data.base_url)

        # Try to fetch models
        models = await fetch_models_from_provider(
            base_url=data.base_url, api_key=data.api_key, headers=data.headers
        )

        return ProviderTestResponse(
            success=True,
            provider_type=provider_type,
            display_name=display_name,
            models_found=len(models),
        )

    except Exception as e:
        return ProviderTestResponse(
            success=False,
            provider_type="unknown",
            display_name="Unknown",
            models_found=0,
            error=str(e),
        )


@router.get("/available/models")
async def get_available_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all available models from all enabled providers."""
    models = get_all_available_models(db)
    return models


@router.post("/{provider_id}/set-default")
async def set_default_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set a provider as the default."""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    # Unset current default
    db.query(Provider).filter(Provider.is_default == True).update({"is_default": False})

    # Set new default
    provider.is_default = True
    db.commit()

    return {"success": True, "provider_id": provider_id}
