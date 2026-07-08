"""Authentication endpoints: login, refresh, logout, me."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserOut,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _parse_login_request(request: Request) -> LoginRequest:
    """Accept JSON `{badge_no, password}` or OAuth2 form `username/password`.

    The form variant keeps the Swagger UI "Authorize" password flow working
    (username maps to badge_no).
    """
    content_type = request.headers.get("content-type", "")
    try:
        if "application/json" in content_type:
            return LoginRequest.model_validate(await request.json())
        form = await request.form()
        badge_no = form.get("username") or form.get("badge_no")
        password = form.get("password")
        return LoginRequest.model_validate({"badge_no": badge_no, "password": password})
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # malformed body
        raise HTTPException(status_code=422, detail="Invalid login payload") from exc


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate by badge number + password and issue access/refresh tokens."""
    creds = await _parse_login_request(request)

    user = await db.scalar(select(User).where(User.badge_no == creds.badge_no))
    if user is None or not verify_password(creds.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid badge number or password")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is inactive")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    payload: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> AccessTokenResponse:
    """Exchange a valid refresh token for a new access token."""
    user_id = decode_token(payload.refresh_token, "refresh")
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return AccessTokenResponse(access_token=create_access_token(user.id))


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)) -> dict:
    """Stateless logout — the client simply discards its tokens."""
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user
