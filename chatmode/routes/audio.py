"""
Audio/Voice asset management routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import math
import aiofiles
from datetime import datetime

from ..database import get_db
from ..models import User, VoiceAsset
from ..schemas import VoiceAssetResponse, VoiceAssetListResponse
from ..auth import get_current_user, require_role
from ..audit import log_action, get_client_ip, AuditAction
from .. import crud

router = APIRouter(prefix="/api/v1/audio", tags=["audio"])

# Configuration
AUDIO_STORAGE_DIR = os.environ.get("AUDIO_STORAGE_DIR", "./data/audio")
MAX_AUDIO_SIZE_MB = int(os.environ.get("MAX_AUDIO_SIZE_MB", "10"))
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
    "audio/m4a": ".m4a",
    "audio/mp4": ".m4a",
}

# Ensure storage directory exists
os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)


def voice_asset_to_response(asset: VoiceAsset) -> VoiceAssetResponse:
    """Convert VoiceAsset model to response schema."""
    return VoiceAssetResponse(
        id=asset.id,
        message_id=asset.message_id,
        filename=asset.filename,
        original_filename=asset.original_filename,
        mime_type=asset.mime_type,
        file_size=asset.file_size,
        duration_seconds=asset.duration_seconds,
        source=asset.source,
        transcript=asset.transcript,
        created_at=asset.created_at
    )


@router.post("/upload", response_model=VoiceAssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    request: Request,
    file: UploadFile = File(...),
    message_id: Optional[str] = None,
    source: str = "user_upload",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an audio file.
    
    - **file**: Audio file (mp3, wav, ogg, webm, m4a)
    - **message_id**: Optional message ID to attach to
    - **source**: Source type (user_upload, tts_generated, recording)
    """
    # Validate content type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "code": "UNSUPPORTED_MEDIA_TYPE",
                "message": f"File type '{content_type}' not allowed. Allowed: {list(ALLOWED_AUDIO_TYPES.keys())}"
            }
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate size
    max_size = MAX_AUDIO_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"File size ({file_size // (1024*1024)}MB) exceeds maximum ({MAX_AUDIO_SIZE_MB}MB)"
            }
        )
    
    # Generate unique filename
    ext = ALLOWED_AUDIO_TYPES.get(content_type, ".mp3")
    asset_id = str(uuid.uuid4())
    filename = f"{asset_id}{ext}"
    file_path = os.path.join(AUDIO_STORAGE_DIR, filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Create database record
    asset = crud.create_voice_asset(
        db=db,
        asset_id=asset_id,
        message_id=message_id,
        filename=filename,
        original_filename=file.filename or "unknown",
        mime_type=content_type,
        file_size=file_size,
        file_path=file_path,
        source=source
    )
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AUDIO_UPLOAD,
        resource_type="voice_asset",
        resource_id=asset_id,
        changes={
            "filename": filename,
            "original_filename": file.filename,
            "size": file_size,
            "source": source
        },
        ip_address=get_client_ip(request)
    )
    
    return voice_asset_to_response(asset)


@router.get("/{asset_id}", response_model=VoiceAssetResponse)
async def get_audio_info(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audio asset metadata."""
    asset = crud.get_voice_asset(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Audio asset not found"}
        )
    
    return voice_asset_to_response(asset)


@router.get("/{asset_id}/stream")
async def stream_audio(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    Stream audio file.
    
    Returns the audio file for inline playback in browsers.
    Supports range requests for seeking.
    """
    asset = crud.get_voice_asset(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Audio asset not found"}
        )
    
    file_path = asset.file_path
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FILE_MISSING", "message": "Audio file not found on disk"}
        )
    
    return FileResponse(
        path=file_path,
        media_type=asset.mime_type,
        filename=asset.original_filename,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": f"inline; filename=\"{asset.original_filename}\""
        }
    )


@router.get("/{asset_id}/download")
async def download_audio(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download audio file as attachment."""
    asset = crud.get_voice_asset(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Audio asset not found"}
        )
    
    file_path = asset.file_path
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FILE_MISSING", "message": "Audio file not found on disk"}
        )
    
    return FileResponse(
        path=file_path,
        media_type=asset.mime_type,
        filename=asset.original_filename,
        headers={
            "Content-Disposition": f"attachment; filename=\"{asset.original_filename}\""
        }
    )


@router.delete("/{asset_id}")
async def delete_audio(
    request: Request,
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "moderator"]))
):
    """Delete an audio asset."""
    asset = crud.get_voice_asset(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Audio asset not found"}
        )
    
    # Delete file from disk
    if os.path.exists(asset.file_path):
        os.remove(asset.file_path)
    
    # Delete from database
    crud.delete_voice_asset(db, asset_id)
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AUDIO_DELETE,
        resource_type="voice_asset",
        resource_id=asset_id,
        changes={"deleted": True, "filename": asset.original_filename},
        ip_address=get_client_ip(request)
    )
    
    return {"status": "deleted", "id": asset_id}


@router.get("/", response_model=VoiceAssetListResponse)
async def list_audio_assets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    message_id: Optional[str] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List audio assets with pagination.
    
    - **message_id**: Filter by message ID
    - **source**: Filter by source type (user_upload, tts_generated, recording)
    """
    assets, total = crud.get_voice_assets(
        db,
        page=page,
        per_page=per_page,
        message_id=message_id,
        source=source
    )
    
    return VoiceAssetListResponse(
        items=[voice_asset_to_response(a) for a in assets],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1
    )


@router.put("/{asset_id}/transcript")
async def update_transcript(
    request: Request,
    asset_id: str,
    transcript: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "moderator"]))
):
    """Update or add a transcript for an audio asset."""
    asset = crud.get_voice_asset(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Audio asset not found"}
        )
    
    # Update transcript
    asset.transcript = transcript
    db.commit()
    db.refresh(asset)
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AUDIO_TRANSCRIPT_UPDATE,
        resource_type="voice_asset",
        resource_id=asset_id,
        changes={"transcript": transcript[:100] + "..." if len(transcript) > 100 else transcript},
        ip_address=get_client_ip(request)
    )
    
    return voice_asset_to_response(asset)


@router.post("/{asset_id}/attach/{message_id}")
async def attach_audio_to_message(
    request: Request,
    asset_id: str,
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Attach an existing audio asset to a message."""
    asset = crud.get_voice_asset(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Audio asset not found"}
        )
    
    # Verify message exists
    message = crud.get_message(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Message not found"}
        )
    
    # Update asset
    asset.message_id = message_id
    db.commit()
    db.refresh(asset)
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AUDIO_ATTACH,
        resource_type="voice_asset",
        resource_id=asset_id,
        changes={"message_id": message_id},
        ip_address=get_client_ip(request)
    )
    
    return {"status": "attached", "asset_id": asset_id, "message_id": message_id}
