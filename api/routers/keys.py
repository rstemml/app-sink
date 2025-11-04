"""
API Key management router
CRUD operations for API keys
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from core.auth import create_api_key, hash_api_key
from models.database import APIKey

router = APIRouter()


class CreateAPIKeyRequest(BaseModel):
    name: str
    description: Optional[str] = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class CreateAPIKeyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    api_key: str  # Only returned on creation
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateAPIKeyRequest(BaseModel):
    is_active: Optional[bool] = None


@router.get("/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db)
):
    """List all API keys (without showing the actual key values)"""
    keys = db.query(APIKey).order_by(APIKey.created_at.desc()).all()
    return keys


@router.post("/keys", response_model=CreateAPIKeyResponse)
async def create_new_api_key(
    request: CreateAPIKeyRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new API key
    Returns the plain API key - save it immediately as it won't be shown again!
    """
    # Check if name already exists
    existing = db.query(APIKey).filter(APIKey.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"API key with name '{request.name}' already exists"
        )

    # Create the key
    plain_key, api_key_record = await create_api_key(
        name=request.name,
        description=request.description,
        db=db
    )

    return CreateAPIKeyResponse(
        id=str(api_key_record.id),
        name=api_key_record.name,
        description=api_key_record.description,
        api_key=plain_key,
        created_at=api_key_record.created_at
    )


@router.patch("/keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    request: UpdateAPIKeyRequest,
    db: Session = Depends(get_db)
):
    """Update API key (e.g., activate/deactivate)"""
    # Find the key
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail=f"API key not found"
        )

    # Update fields
    if request.is_active is not None:
        api_key.is_active = request.is_active

    db.commit()
    db.refresh(api_key)

    return api_key


@router.delete("/keys/{key_id}")
async def delete_api_key(
    key_id: str,
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    # Find the key
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail=f"API key not found"
        )

    db.delete(api_key)
    db.commit()

    return {"message": "API key deleted successfully"}
