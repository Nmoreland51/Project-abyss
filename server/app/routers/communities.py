"""Communities, subscriptions and role-based moderator membership (R03)."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import cursor as cur
from ..config import get_settings
from ..db import get_db
from ..deps import Principal, optional_principal, require_principal
from ..errors import ApiError, conflict, forbidden, not_found
from ..models import Community, Membership, User
from ..ratelimit import limiter
from ..schemas import Community as CommunitySchema
from ..schemas import (
    CommunityPage,
    CreateCommunityRequest,
    Moderator,
    UpdateCommunityRequest,
    UserRef,
)
from ..text import clean_text, normalize_handle, validate_slug
from ..views import community_view, get_active_community, membership_of

router = APIRouter(tags=["communities"])


def _rules(rules) -> list[dict]:
    return [
        {
            "title": clean_text(r.title, field="rules.title", max_len=100, min_len=1, multiline=False),
            "description": clean_text(r.description, field="rules.description", max_len=500),
        }
        for r in rules
    ]


@router.get("/v1/communities", response_model=CommunityPage)
def list_communities(
    q: str | None = Query(default=None, max_length=50, description="Prefix filter on community name"),
    cursor: str | None = Query(default=None, max_length=512),
    limit: int = Query(default=25, ge=1, le=100),
    principal: Principal | None = Depends(optional_principal),
    db: Session = Depends(get_db),
) -> CommunityPage:
    stmt = select(Community).where(Community.status == "active")
    if q:
        prefix = q.strip().lower().replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
        stmt = stmt.where(Community.slug.like(f"{prefix}%", escape="\\"))
    c = cur.decode(cursor, "communities")
    if c:
        stmt = stmt.where(
            or_(
                Community.subscriber_count < c["v"],
                and_(Community.subscriber_count == c["v"], Community.id < uuid.UUID(c["id"])),
            )
        )
    rows = db.scalars(stmt.order_by(Community.subscriber_count.desc(), Community.id.desc()).limit(limit + 1)).all()
    more = len(rows) > limit
    rows = rows[:limit]
    viewer = principal.user.id if principal else None
    items = [community_view(r, membership_of(db, viewer, r.id)) for r in rows]
    next_cursor = (
        cur.encode({"k": "communities", "v": rows[-1].subscriber_count, "id": str(rows[-1].id)}) if more else None
    )
    return CommunityPage(items=items, next_cursor=next_cursor)


@router.post("/v1/communities", response_model=CommunitySchema, status_code=201)
def create_community(
    body: CreateCommunityRequest, principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> CommunitySchema:
    slug = validate_slug(body.slug)
    display = clean_text(body.display_name or slug, field="display_name", max_len=100, min_len=1, multiline=False)
    # Counted after validation so typos in a name do not consume the allowance.
    limiter.check(
        f"community-create:{principal.user.id}", get_settings().community_create_per_hour, window_seconds=3600
    )
    now = datetime.now(UTC)
    community = Community(
        id=uuid.uuid4(),
        slug=slug,
        display_name=display,
        description=clean_text(body.description, field="description", max_len=5000),
        rules=_rules(body.rules),
        created_by=principal.user.id,
        status="active",
        subscriber_count=1,
        created_at=now,
    )
    db.add(community)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("slug_taken", "A community with that name already exists") from exc
    m = Membership(user_id=principal.user.id, community_id=community.id, role="owner", subscribed=True, created_at=now)
    db.add(m)
    db.commit()
    return community_view(community, m)


@router.get("/v1/communities/{slug}", response_model=CommunitySchema)
def get_community(
    slug: str, principal: Principal | None = Depends(optional_principal), db: Session = Depends(get_db)
) -> CommunitySchema:
    c = get_active_community(db, slug)
    return community_view(c, membership_of(db, principal.user.id if principal else None, c.id))


@router.patch("/v1/communities/{slug}", response_model=CommunitySchema)
def update_community(
    slug: str,
    body: UpdateCommunityRequest,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> CommunitySchema:
    c = get_active_community(db, slug, lock=True)
    m = membership_of(db, principal.user.id, c.id)
    if not principal.user.is_admin and (m is None or m.role not in ("moderator", "owner")):
        raise forbidden("Only moderators can edit this community")
    if body.display_name is not None:
        c.display_name = clean_text(body.display_name, field="display_name", max_len=100, min_len=1, multiline=False)
    if body.description is not None:
        c.description = clean_text(body.description, field="description", max_len=5000)
    if body.rules is not None:
        c.rules = _rules(body.rules)
    db.commit()
    return community_view(c, m)


@router.put("/v1/communities/{slug}/membership", response_model=CommunitySchema)
def subscribe(
    slug: str, principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> CommunitySchema:
    """Idempotent: subscribing twice leaves one membership and an unchanged count."""
    limiter.check(f"write:{principal.user.id}", get_settings().write_rate_limit_per_minute)
    c = get_active_community(db, slug, lock=True)
    m = membership_of(db, principal.user.id, c.id)
    if m is None:
        m = Membership(user_id=principal.user.id, community_id=c.id, role="member", subscribed=True)
        m.created_at = datetime.now(UTC)
        db.add(m)
        c.subscriber_count += 1
    elif not m.subscribed:
        m.subscribed = True
        c.subscriber_count += 1
    db.commit()
    return community_view(c, m)


@router.delete("/v1/communities/{slug}/membership", response_model=CommunitySchema)
def unsubscribe(
    slug: str, principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> CommunitySchema:
    """Idempotent. Moderator/owner roles are retained (roles are separate from subscription)."""
    c = get_active_community(db, slug, lock=True)
    m = membership_of(db, principal.user.id, c.id)
    if m is not None and m.subscribed:
        c.subscriber_count = max(0, c.subscriber_count - 1)
        if m.role == "member":
            db.delete(m)
            m = None
        else:
            m.subscribed = False
    db.commit()
    return community_view(c, m)


@router.get("/v1/communities/{slug}/moderators", response_model=list[Moderator])
def list_moderators(slug: str, db: Session = Depends(get_db)) -> list[Moderator]:
    c = get_active_community(db, slug)
    rows = db.execute(
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.community_id == c.id, Membership.role.in_(("moderator", "owner")), User.status != "deleted")
        .order_by(Membership.role.desc(), Membership.created_at)
    ).all()
    return [Moderator(user=UserRef(id=u.id, handle=u.handle), role=m.role) for m, u in rows]


def _owner_only(db: Session, principal: Principal, c: Community) -> None:
    m = membership_of(db, principal.user.id, c.id)
    if not principal.user.is_admin and (m is None or m.role != "owner"):
        raise forbidden("Only the community owner can change moderators")


@router.put("/v1/communities/{slug}/moderators/{handle}", response_model=list[Moderator])
def add_moderator(
    slug: str, handle: str, principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> list[Moderator]:
    c = get_active_community(db, slug, lock=True)
    _owner_only(db, principal, c)
    target = db.scalar(select(User).where(User.handle_norm == normalize_handle(handle), User.status == "active"))
    if target is None:
        raise not_found("User")
    m = membership_of(db, target.id, c.id)
    if m is None:
        db.add(Membership(user_id=target.id, community_id=c.id, role="moderator", subscribed=False))
    elif m.role == "member":
        m.role = "moderator"
    db.commit()
    return list_moderators(slug, db)


@router.delete("/v1/communities/{slug}/moderators/{handle}", response_model=list[Moderator])
def remove_moderator(
    slug: str, handle: str, principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> list[Moderator]:
    c = get_active_community(db, slug, lock=True)
    _owner_only(db, principal, c)
    target = db.scalar(select(User).where(User.handle_norm == normalize_handle(handle)))
    m = membership_of(db, target.id, c.id) if target else None
    if m is None or m.role == "member":
        raise not_found("Moderator")
    if m.role == "owner":
        raise ApiError(409, "owner_required", "The owner role cannot be removed; transfer ownership first")
    if m.subscribed:
        m.role = "member"
    else:
        db.delete(m)
    db.commit()
    return list_moderators(slug, db)


@router.get("/v1/me/communities", response_model=list[CommunitySchema], tags=["me"])
def my_communities(principal: Principal = Depends(require_principal), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Community, Membership)
        .join(Membership, Membership.community_id == Community.id)
        .where(Membership.user_id == principal.user.id, Community.status == "active")
        .where(or_(Membership.subscribed.is_(True), Membership.role != "member"))
        .order_by(Community.slug)
        .limit(500)
    ).all()
    return [community_view(c, m) for c, m in rows]
