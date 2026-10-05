"""Feature T1 · Sign up and account. Owner: Person 1.

Already working, because every other person needs login and the role check from day one.
"""

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.accounts.models import User
from app.modules.accounts.schemas import (
    LoginIn,
    RefreshIn,
    RegisterIn,
    TokensOut,
    UpdateMeIn,
    UserOut,
)

router = APIRouter(tags=["T1 · Accounts"])


def _tokens(user: User) -> TokensOut:
    return TokensOut(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
        role=user.role,
    )


@router.post("/auth/register", response_model=TokensOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)) -> TokensOut:
    """Why: a traveler needs an account to save trips and chat history.
    Then: login, and every trip gets a user_id."""
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(
        name=body.name,
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        role="traveler",
        language=body.language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _tokens(user)


@router.post("/auth/login", response_model=TokensOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokensOut:
    """Why: returns the token every protected endpoint checks.
    Then: all other people use this token in their routes."""
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password")
    return _tokens(user)


@router.post("/auth/refresh", response_model=TokensOut)
def refresh(body: RefreshIn, db: Session = Depends(get_db)) -> TokensOut:
    """Why: access tokens expire quickly for safety.
    Then: the front end stays logged in without asking for the password again."""
    try:
        payload = decode_token(body.refresh_token, "refresh")
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from exc
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return _tokens(user)


@router.post("/auth/logout", status_code=204)
def logout(_: User = Depends(get_current_user)) -> None:
    """Why: ends the session on shared devices.
    TODO(Person 1): store revoked refresh tokens if we need server-side logout.
    For now the client deletes its tokens."""


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    """Why: the app needs to know who is logged in and their role.
    Then: the front end shows the traveler, company or admin interface based on role."""
    return user


@router.patch("/me", response_model=UserOut)
def update_me(body: UpdateMeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """Why: users change name, language or password."""
    if body.name is not None:
        user.name = body.name
    if body.language is not None:
        user.language = body.language
    if body.new_password is not None:
        if not body.current_password or not verify_password(body.current_password, user.password_hash):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is wrong")
        user.password_hash = hash_password(body.new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
