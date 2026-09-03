from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from .core.security import decode_token
from .db import get_session
from .models import Role, User
bearer = HTTPBearer(auto_error=False)
def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), session: Session = Depends(get_session)) -> User:
    if not credentials: raise HTTPException(401, "Authentication required")
    try:
        claims = decode_token(credentials.credentials)
    except (ValueError, KeyError, TypeError):
        raise HTTPException(401, "Invalid or expired token") from None
    user = session.scalar(select(User).where(User.username == claims["sub"]))
    if not user or not user.active: raise HTTPException(401, "Inactive user")
    return user
def require_roles(*allowed: str):
    def check(user: User = Depends(current_user), session: Session = Depends(get_session)) -> User:
        role = session.get(Role, user.role_id)
        if not role or role.name not in allowed: raise HTTPException(403, "Insufficient role")
        return user
    return check
