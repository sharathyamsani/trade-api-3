"""
JWT-based authentication helpers.
Supports both issued tokens and guest (unauthenticated) access.
"""
import time
import uuid
import logging

import jwt
from fastapi import HTTPException, status

from config import settings

logger = logging.getLogger(__name__)


def create_guest_token() -> tuple[str, str]:
    """Create a guest JWT and return (token, session_id)."""
    session_id = str(uuid.uuid4())
    payload = {
        "sub": session_id,
        "role": "guest",
        "iat": time.time(),
        "exp": time.time() + settings.JWT_EXPIRE_MINUTES * 60,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, session_id


def verify_token(token: str) -> str:
    """Verify JWT and return the session_id (sub claim)."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        session_id: str = payload.get("sub", "")
        if not session_id:
            raise ValueError("Missing sub claim")
        return session_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Request a new one at POST /auth/token",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )
