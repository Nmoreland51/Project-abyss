"""Registration, login, refresh-token rotation (with reuse detection), logout, sessions."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..deps import Principal, require_principal
from ..errors import ApiError, conflict, not_found, unauthorized
from ..models import AuthSession, User
from ..ratelimit import client_ip, limiter
from ..schemas import (
    AuthResponse,
    LoginRequest,
    Me,
    RefreshRequest,
    RegisterRequest,
    SessionInfo,
    TokenPair,
    UpdateMeRequest,
)
from ..security import hash_password, needs_rehash, new_token, token_digest, verify_password
from ..text import clean_text, normalize_handle, validate_new_handle, validate_password

router = APIRouter(tags=["auth"])

# A client whose refresh response was lost in transit may retry with the previous token.
# Within this window that retry rotates again instead of being treated as theft (ADR-0002).
REFRESH_REUSE_GRACE_SECONDS = 30


def me_view(user: User) -> Me:
    return Me(
        id=user.id,
        handle=user.handle,
        display_name=user.display_name,
        bio=user.bio,
        post_karma=user.post_karma,
        comment_karma=user.comment_karma,
        created_at=user.created_at,
        is_admin=user.is_admin,
    )


def _issue(db: Session, user: User, request: Request, session: AuthSession | None = None) -> TokenPair:
    settings = get_settings()
    now = datetime.now(UTC)
    access, refresh = new_token("at"), new_token("rt")
    access_exp = now + timedelta(seconds=settings.access_token_ttl_seconds)
    refresh_exp = now + timedelta(seconds=settings.refresh_token_ttl_seconds)
    if session is None:
        session = AuthSession(
            id=uuid.uuid4(),
            user_id=user.id,
            user_agent=(request.headers.get("user-agent") or "")[:200] or None,
            created_at=now,
            last_used_at=now,
        )
        db.add(session)
    else:
        session.prev_refresh_hash = session.refresh_hash
    session.access_hash = token_digest(access)
    session.access_expires_at = access_exp
    session.refresh_hash = token_digest(refresh)
    session.refresh_expires_at = refresh_exp
    session.rotated_at = now
    session.last_used_at = now
    return TokenPair(
        access_token=access,
        access_expires_at=access_exp,
        refresh_token=refresh,
        refresh_expires_at=refresh_exp,
        session_id=session.id,
    )


def _auth_limits(request: Request, handle: str) -> None:
    limit = get_settings().auth_rate_limit_per_minute
    limiter.check(f"auth-ip:{client_ip(request)}", limit)
    limiter.check(f"auth-handle:{handle.strip().lower()[:40]}", limit)


@router.post("/v1/auth/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> AuthResponse:
    _auth_limits(request, body.handle)
    handle, norm = validate_new_handle(body.handle)
    validate_password(body.password, norm)
    if db.scalar(select(User.id).where(User.handle_norm == norm)) is not None:
        raise conflict("handle_taken", "That handle is already taken")
    user = User(id=uuid.uuid4(), handle=handle, handle_norm=norm, password_hash=hash_password(body.password))
    user.created_at = datetime.now(UTC)
    user.post_karma = user.comment_karma = 0
    user.is_admin = False
    user.status = "active"
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("handle_taken", "That handle is already taken") from exc
    tokens = _issue(db, user, request)
    db.commit()
    return AuthResponse(user=me_view(user), tokens=tokens)


@router.post("/v1/auth/login", response_model=AuthResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)) -> AuthResponse:
    _auth_limits(request, body.handle)
    try:
        norm = normalize_handle(body.handle)
    except ApiError:
        norm = None
    user = db.scalar(select(User).where(User.handle_norm == norm)) if norm else None
    if not verify_password(user.password_hash if user else None, body.password) or user is None:
        raise unauthorized("Incorrect handle or password")
    if user.status != "active":
        raise ApiError(403, "account_inactive", "Account is not active")
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    tokens = _issue(db, user, request)
    db.commit()
    return AuthResponse(user=me_view(user), tokens=tokens)


@router.post("/v1/auth/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    limiter.check(f"refresh-ip:{client_ip(request)}", get_settings().auth_rate_limit_per_minute * 3)
    digest = token_digest(body.refresh_token)
    now = datetime.now(UTC)
    session = db.scalar(select(AuthSession).where(AuthSession.refresh_hash == digest).with_for_update())
    if session is None:
        reused = db.scalar(select(AuthSession).where(AuthSession.prev_refresh_hash == digest).with_for_update())
        if reused is None or reused.revoked_at is not None:
            raise unauthorized("Invalid refresh token")
        if now - reused.rotated_at > timedelta(seconds=REFRESH_REUSE_GRACE_SECONDS):
            # Reuse of an already-rotated refresh token outside the grace window indicates theft.
            reused.revoked_at = now
            reused.revoked_reason = "refresh_reuse"
            db.commit()
            raise unauthorized("Refresh token reuse detected; session revoked")
        # Inside the grace window (e.g. the previous response was lost): rotate again.
        session = reused
    if session.revoked_at is not None or session.refresh_expires_at <= now:
        raise unauthorized("Session expired or revoked; log in again")
    user = db.get(User, session.user_id)
    if user is None or user.status != "active":
        raise unauthorized("Account is not active")
    tokens = _issue(db, user, request, session)
    db.commit()
    return tokens


@router.post("/v1/auth/logout", status_code=204)
def logout(principal: Principal = Depends(require_principal), db: Session = Depends(get_db)) -> Response:
    db.execute(
        update(AuthSession)
        .where(AuthSession.id == principal.session.id)
        .values(revoked_at=datetime.now(UTC), revoked_reason="logout")
    )
    db.commit()
    return Response(status_code=204)


@router.get("/v1/me", response_model=Me, tags=["me"])
def get_me(principal: Principal = Depends(require_principal)) -> Me:
    return me_view(principal.user)


@router.patch("/v1/me", response_model=Me, tags=["me"])
def patch_me(
    body: UpdateMeRequest, principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> Me:
    user = db.get(User, principal.user.id)
    assert user is not None
    if body.display_name is not None:
        user.display_name = clean_text(body.display_name, field="display_name", max_len=50, multiline=False) or None
    if body.bio is not None:
        user.bio = clean_text(body.bio, field="bio", max_len=500) or None
    db.commit()
    return me_view(user)


@router.get("/v1/me/sessions", response_model=list[SessionInfo], tags=["me"])
def list_sessions(principal: Principal = Depends(require_principal), db: Session = Depends(get_db)):
    now = datetime.now(UTC)
    rows = db.scalars(
        select(AuthSession)
        .where(
            AuthSession.user_id == principal.user.id,
            AuthSession.revoked_at.is_(None),
            AuthSession.refresh_expires_at > now,
        )
        .order_by(AuthSession.last_used_at.desc())
    ).all()
    return [
        SessionInfo(
            id=s.id,
            created_at=s.created_at,
            last_used_at=s.last_used_at,
            user_agent=s.user_agent,
            current=s.id == principal.session.id,
        )
        for s in rows
    ]


@router.delete("/v1/me/sessions/{session_id}", status_code=204, tags=["me"])
def revoke_session(
    session_id: uuid.UUID, principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> Response:
    result = db.execute(
        update(AuthSession)
        .where(
            AuthSession.id == session_id,
            AuthSession.user_id == principal.user.id,
            AuthSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC), revoked_reason="user_revoked")
    )
    db.commit()
    if result.rowcount == 0:
        raise not_found("Session")
    return Response(status_code=204)
