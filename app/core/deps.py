"""Shared FastAPI dependencies: database session, current user, role checks.

Owner: Person 1. Everyone uses these in their routers:

    @router.get("/something")
    def handler(user: User = Depends(require_role("traveler")), db: Session = Depends(get_db)):
        ...
"""

from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.modules.accounts.models import User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    try:
        payload = decode_token(creds.credentials, "access")
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def require_role(*roles: str) -> Callable[..., User]:
    """Dependency factory: require_role("admin"), require_role("company"), require_role("traveler", "admin")."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires role: {', '.join(roles)}")
        return user

    return checker


def not_implemented(owner: str) -> HTTPException:
    """Placeholder for endpoints not built yet. Replace the `raise not_implemented(...)` line with real code."""
    return HTTPException(status.HTTP_501_NOT_IMPLEMENTED, f"Not implemented yet (owner: {owner})")
