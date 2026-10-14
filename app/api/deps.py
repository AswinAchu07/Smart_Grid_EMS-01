"""Authentication dependencies and Role-Based Access Control (RBAC) checkers.
"""

from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.core.constants import UserRole
from app.db.session import get_db
from app.db.models import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Retrieve user if valid Bearer token provided; else None (for public/permissive access)."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    email: str = payload["sub"]
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        return None
    return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Enforce valid Bearer authentication token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception
    email: str = payload["sub"]
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account")
    return user


def require_role(allowed_roles: List[UserRole]):
    """RBAC dependency factory checking if current user possesses necessary role."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_values = [r.value for r in allowed_roles]
        if current_user.role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {role_values}, current role: {current_user.role}",
            )
        return current_user
    return role_checker
