"""
API Dependencies - Authentication and Authorization

Provides FastAPI dependencies for protecting routes.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Literal

from backend.models.auth import User, TokenData
from backend.utils.security import decode_access_token
from backend.utils.user_store import get_user_store


# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Raises HTTPException 401 if token is invalid or user not found.
    """
    token = credentials.credentials

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Get user from store
    user_store = get_user_store()
    user_in_db = user_store.get_user(username)

    if user_in_db is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if user_in_db.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Return user without password
    return User(**user_in_db.model_dump(exclude={"hashed_password"}))


async def require_role(required_role: Literal["admin", "user", "prompt_engineer"]):
    """
    Dependency factory to require a specific role.

    Usage:
        @router.get("/admin/endpoint", dependencies=[Depends(require_role("admin"))])
    """
    async def check_role(user: User = Depends(get_current_user)):
        # Admin has access to everything
        if user.role == "admin":
            return user

        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role"
            )

        return user

    return check_role


# Convenience dependencies for common roles

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


async def require_prompt_engineer(user: User = Depends(get_current_user)) -> User:
    """Require prompt_engineer or admin role"""
    if user.role not in ["admin", "prompt_engineer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Prompt engineer access required"
        )
    return user


async def require_authenticated(user: User = Depends(get_current_user)) -> User:
    """Require any authenticated user"""
    return user
