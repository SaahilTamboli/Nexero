"""
Authentication utilities for protected dashboard endpoints.

This module validates Supabase-issued JWT bearer tokens.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def _decode_supabase_jwt(token: str, jwt_secret: str) -> Dict[str, Any]:
    """Decode Supabase JWT token and return claims."""
    try:
        return jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as primary_error:
        # Fallback for tokens without aud claim in legacy setups.
        try:
            return jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except JWTError:
            raise primary_error


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    Validate bearer token and return normalized user payload.

    If REQUIRE_DASHBOARD_AUTH is disabled, this returns a synthetic user.
    """
    settings = get_settings()

    if not settings.REQUIRE_DASHBOARD_AUTH:
        return {
            "id": "dev-user",
            "email": None,
            "role": "service_role",
            "claims": {},
        }

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Authorization token is required",
                "code": "UNAUTHORIZED",
            },
        )

    if not settings.SUPABASE_JWT_SECRET:
        logger.error("SUPABASE_JWT_SECRET is missing while auth is required")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Server auth configuration is incomplete",
                "code": "AUTH_CONFIG_ERROR",
            },
        )

    token = credentials.credentials

    try:
        payload = _decode_supabase_jwt(token=token, jwt_secret=settings.SUPABASE_JWT_SECRET)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Invalid or expired token",
                "code": "INVALID_TOKEN",
            },
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token subject is missing",
                "code": "INVALID_TOKEN",
            },
        )

    return {
        "id": user_id,
        "email": payload.get("email"),
        "role": payload.get("role"),
        "claims": payload,
    }
