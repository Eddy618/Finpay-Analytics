import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from pwdlib import PasswordHash
from sqlalchemy import text

from api.database import engine


router = APIRouter(prefix="/auth", tags=["Authentication"])

password_hash = PasswordHash.recommended()

security = HTTPBearer(auto_error=False)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY is missing from environment configuration."
    )


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in_minutes: int
    username: str
    role: str


class CurrentUser(BaseModel):
    user_id: int
    username: str
    role: str


def create_access_token(
    user_id: int,
    username: str,
    role: str,
) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=JWT_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    query = text(
        """
        SELECT
            user_id,
            username,
            password_hash,
            role,
            is_active
        FROM public.app_users
        WHERE username = :username
        LIMIT 1
        """
    )

    with engine.connect() as conn:
        user = conn.execute(
            query,
            {"username": request.username.strip()},
        ).mappings().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    try:
        password_valid = password_hash.verify(
            request.password,
            user["password_hash"],
        )
    except Exception:
        password_valid = False

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_access_token(
        user_id=user["user_id"],
        username=user["username"],
        role=user["role"],
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=JWT_EXPIRE_MINUTES,
        username=user["username"],
        role=user["role"],
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")

    if not user_id or not username or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = text(
        """
        SELECT
            user_id,
            username,
            role,
            is_active
        FROM public.app_users
        WHERE user_id = :user_id
        LIMIT 1
        """
    )

    with engine.connect() as conn:
        user = conn.execute(
            query,
            {"user_id": int(user_id)},
        ).mappings().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return CurrentUser(
        user_id=user["user_id"],
        username=user["username"],
        role=user["role"],
    )


def require_roles(*allowed_roles: str):
    def role_dependency(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return role_dependency