"""
Authentication and API key management
"""

import secrets
import hashlib
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.database import get_db
from models.database import APIKey

security = HTTPBearer()


def generate_api_key(name: str = "default") -> str:
    """
    Generate a new API key
    Format: ask_<64 random chars>
    """
    random_part = secrets.token_urlsafe(48)  # 64 chars when base64 encoded
    api_key = f"ask_{random_part}"
    return api_key


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> APIKey:
    """
    Verify API key from Authorization header
    Usage: Bearer ask_xxxxxxxxxxxx
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication credentials"
        )

    token = credentials.credentials

    if not token.startswith("ask_"):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key format"
        )

    # Hash the provided key
    key_hash = hash_api_key(token)

    # Look up in database
    api_key_record = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()

    if not api_key_record:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key"
        )

    # Update last used timestamp
    api_key_record.last_used_at = datetime.utcnow()
    db.commit()

    return api_key_record


async def create_api_key(
    name: str,
    description: Optional[str] = None,
    db: Session = None
) -> tuple[str, APIKey]:
    """
    Create a new API key in the database
    Returns: (plain_api_key, api_key_record)
    """
    plain_key = generate_api_key(name)
    key_hash = hash_api_key(plain_key)

    api_key_record = APIKey(
        name=name,
        description=description,
        key_hash=key_hash,
        is_active=True,
        created_at=datetime.utcnow()
    )

    db.add(api_key_record)
    db.commit()
    db.refresh(api_key_record)

    return plain_key, api_key_record
