"""
Authentication Routes - Login and Token Management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta

from backend.models.auth import LoginRequest, TokenResponse, User
from backend.utils.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_HOURS
from backend.utils.user_store import get_user_store
from backend.api.dependencies import require_authenticated


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Login with username and password.

    Returns:
        JWT access token

    Raises:
        401: If credentials are invalid
    """
    user_store = get_user_store()

    # Get user
    user = user_store.get_user(credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Check if disabled
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "permissions": user.permissions
        },
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600
    )


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(credentials: LoginRequest):
    """
    Register a new user account.

    Note: In production, you may want to disable this or add admin-only restriction.

    Returns:
        Created user (without password)

    Raises:
        400: If username already exists
    """
    from backend.models.auth import UserInDB
    from backend.utils.security import get_password_hash

    user_store = get_user_store()

    # Check if user exists
    if user_store.get_user(credentials.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create user
    new_user = UserInDB(
        username=credentials.username,
        hashed_password=get_password_hash(credentials.password),
        role="user",  # Default role
        permissions=[]
    )

    success = user_store.create_user(new_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    # Return user without password
    return User(**new_user.model_dump(exclude={"hashed_password"}))


@router.get("/me", response_model=User)
async def get_current_user_info(
    user: User = Depends(require_authenticated)
):
    """
    Get current user information.

    Requires:
        Valid JWT token in Authorization header

    Returns:
        Current user data
    """
    return user
