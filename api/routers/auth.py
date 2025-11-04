"""
Authentication router
Simple JWT-based authentication for the web dashboard
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import jwt
import os

router = APIRouter()
security = HTTPBasic()

# JWT Settings (for demo purposes - should be in config)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Demo credentials (should be in database with hashed passwords)
DEMO_USERS = {
    "admin": "admin",  # username: password
    "demo": "demo123"
}


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Login endpoint for web dashboard
    For demo purposes, uses hardcoded credentials
    In production, this should verify against a proper user database
    """
    # Verify credentials
    if credentials.username not in DEMO_USERS:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if DEMO_USERS[credentials.username] != credentials.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": credentials.username}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )
