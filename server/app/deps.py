"""Authentication dependencies. Every write route depends on `require_principal`; reads use
`optional_principal` so anonymous users can browse public content (R01)."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .db import get_db
from .errors import ApiError, forbidden, unauthorized
from .models import AuthSession, User
from .security import token_digest


@dataclass
class Principal:
    user: User
    session: AuthSession


def _bearer(request: Request) -> str | None:
    header = request.headers.get("authorization")
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise unauthorized("Malformed Authorization header")
    return token.strip()


def _resolve(db: Session, token: str) -> Principal:
    now = datetime.now(UTC)
    row = db.execute(
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(AuthSession.access_hash == token_digest(token))
    ).first()
    if row is None:
        raise unauthorized("Invalid access token")
    session, user = row
    if session.revoked_at is not None:
        raise unauthorized("Session has been revoked")
    if session.access_expires_at <= now:
        raise ApiError(401, "token_expired", "Access token expired; refresh and retry")
    if user.status != "active":
        raise forbidden("Account is not active")
    # Throttle last_used writes to at most once per minute per session.
    if now - session.last_used_at > timedelta(minutes=1):
        db.execute(update(AuthSession).where(AuthSession.id == session.id).values(last_used_at=now))
        db.commit()
    return Principal(user=user, session=session)


def optional_principal(request: Request, db: Session = Depends(get_db)) -> Principal | None:
    token = _bearer(request)
    return None if token is None else _resolve(db, token)


def require_principal(request: Request, db: Session = Depends(get_db)) -> Principal:
    token = _bearer(request)
    if token is None:
        raise unauthorized()
    return _resolve(db, token)
