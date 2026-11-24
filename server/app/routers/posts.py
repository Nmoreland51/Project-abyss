"""Posts and feeds (R01, R04, R07). Feeds use keyset pagination over stored rank columns."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy import Select, select, tuple_
from sqlalchemy.orm import Session

from .. import cursor as cur
from .. import idempotency
from ..config import get_settings
from ..db import get_db
from ..deps import Principal, optional_principal, require_principal
from ..errors import conflict, forbidden, invalid, not_found
from ..models import Community, Membership, ModerationAction, Post, User
from ..ranking import CONTROVERSY_FORMULA_VERSION, HOT_FORMULA_VERSION, hot_rank
from ..ratelimit import limiter
from ..schemas import CreatePostRequest, PostPage, PostSort, TimeWindow, UpdatePostRequest
from ..schemas import Post as PostSchema
from ..text import clean_text, normalize_handle, validate_link
from ..views import get_active_community, get_post, is_moderator, post_views

router = APIRouter(tags=["posts"])

WINDOWS = {
    "hour": timedelta(hours=1),
    "day": timedelta(days=1),
    "week": timedelta(weeks=1),
    "month": timedelta(days=30),
    "year": timedelta(days=365),
}
SORT_COLUMNS = {
    "new": Post.created_at,
    "hot": Post.hot_rank,
    "top": Post.score,
    "controversial": Post.controversy,
}


def _ranking_version(sort: str) -> str:
    return {"hot": HOT_FORMULA_VERSION, "controversial": CONTROVERSY_FORMULA_VERSION}.get(sort, f"{sort}-v1")


def _cursor_value(sort: str, c: dict):
    """Validate the type of an untrusted cursor's sort value before it reaches SQL."""
    v = c.get("v")
    try:
        if not isinstance(c.get("at"), str):
            raise ValueError
        if sort == "new":
            return datetime.fromisoformat(v)
        if sort == "top" and isinstance(v, int) and not isinstance(v, bool):
            return v
        if sort in ("hot", "controversial") and isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    except (TypeError, ValueError):
        pass
    raise invalid("Invalid or expired cursor", "cursor")


def post_page(
    db: Session,
    stmt: Select,
    *,
    sort: PostSort,
    t: TimeWindow,
    cursor: str | None,
    limit: int,
    viewer: uuid.UUID | None,
    scope: str,
) -> PostPage:
    col = SORT_COLUMNS[sort]
    c = cur.decode(cursor, f"posts:{sort}:{t}:{scope}")
    last = None
    if c:
        last = _cursor_value(sort, c)
        as_of = datetime.fromisoformat(c["at"])
    else:
        as_of = datetime.now(UTC)
    stmt = stmt.where(Post.state == "visible", Post.created_at <= as_of)
    if sort in ("top", "controversial") and t != "all":
        stmt = stmt.where(Post.created_at >= as_of - WINDOWS[t])
    if c:
        stmt = stmt.where(tuple_(col, Post.id) < tuple_(last, uuid.UUID(c["id"])))
    rows = db.scalars(stmt.order_by(col.desc(), Post.id.desc()).limit(limit + 1)).all()
    more = len(rows) > limit
    rows = list(rows[:limit])
    next_cursor = None
    if more:
        tail = rows[-1]
        value = tail.created_at.isoformat() if sort == "new" else getattr(tail, col.key)
        next_cursor = cur.encode(
            {"k": f"posts:{sort}:{t}:{scope}", "v": value, "id": str(tail.id), "at": as_of.isoformat()}
        )
    return PostPage(
        items=post_views(db, rows, viewer),
        next_cursor=next_cursor,
        sort=sort,
        time_window=t,
        scope=scope,
        ranking_version=_ranking_version(sort),
    )


def _visible_posts() -> Select:
    return select(Post).join(Community, Community.id == Post.community_id).where(Community.status == "active")


@router.get("/v1/feed", response_model=PostPage, tags=["feeds"])
def feed(
    scope: str = Query(default="home", pattern="^(home|all)$"),
    sort: PostSort = "hot",
    t: TimeWindow = "day",
    cursor: str | None = Query(default=None, max_length=512),
    limit: int = Query(default=25, ge=1, le=100),
    principal: Principal | None = Depends(optional_principal),
    db: Session = Depends(get_db),
) -> PostPage:
    """`home` = subscribed communities (anonymous users get `all`). `t` applies to top/controversial."""
    viewer = principal.user.id if principal else None
    stmt = _visible_posts()
    effective = scope if viewer else "all"
    if effective == "home":
        subs = select(Membership.community_id).where(Membership.user_id == viewer, Membership.subscribed.is_(True))
        stmt = stmt.where(Post.community_id.in_(subs))
    if sort in ("hot", "new"):
        t = "all"
    return post_page(db, stmt, sort=sort, t=t, cursor=cursor, limit=limit, viewer=viewer, scope=effective)


@router.get("/v1/communities/{slug}/posts", response_model=PostPage, tags=["feeds"])
def community_posts(
    slug: str,
    sort: PostSort = "hot",
    t: TimeWindow = "day",
    cursor: str | None = Query(default=None, max_length=512),
    limit: int = Query(default=25, ge=1, le=100),
    principal: Principal | None = Depends(optional_principal),
    db: Session = Depends(get_db),
) -> PostPage:
    c = get_active_community(db, slug)
    if sort in ("hot", "new"):
        t = "all"
    stmt = _visible_posts().where(Post.community_id == c.id)
    viewer = principal.user.id if principal else None
    return post_page(db, stmt, sort=sort, t=t, cursor=cursor, limit=limit, viewer=viewer, scope=f"c/{c.slug}")


@router.get("/v1/users/{handle}/posts", response_model=PostPage, tags=["users"])
def user_posts(
    handle: str,
    cursor: str | None = Query(default=None, max_length=512),
    limit: int = Query(default=25, ge=1, le=100),
    principal: Principal | None = Depends(optional_principal),
    db: Session = Depends(get_db),
) -> PostPage:
    user = db.scalar(select(User).where(User.handle_norm == normalize_handle(handle), User.status == "active"))
    if user is None:
        raise not_found("User")
    stmt = _visible_posts().where(Post.author_id == user.id)
    viewer = principal.user.id if principal else None
    return post_page(db, stmt, sort="new", t="all", cursor=cursor, limit=limit, viewer=viewer, scope=f"u/{user.id}")


@router.post("/v1/posts", response_model=PostSchema, status_code=201)
def create_post(
    body: CreatePostRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
):
    limiter.check(f"write:{principal.user.id}", get_settings().write_rate_limit_per_minute)
    replay = idempotency.begin(db, principal.user.id, idempotency_key, "create_post", body.model_dump())
    if replay is not None:
        return replay
    community = get_active_community(db, body.community)
    title = clean_text(body.title, field="title", max_len=300, min_len=1, multiline=False)
    flair = clean_text(body.flair, field="flair", max_len=64, multiline=False) or None
    text_body, url = None, None
    if body.kind == "text":
        if body.url:
            raise invalid("Text posts cannot include a URL; use kind=link", "url")
        text_body = clean_text(body.body, field="body", max_len=40000) or None
    else:
        if not body.url:
            raise invalid("Link posts require a URL", "url")
        if body.body:
            raise invalid("Link posts cannot include a body", "body")
        url = validate_link(body.url)
    now = datetime.now(UTC)
    post = Post(
        id=uuid.uuid4(),
        community_id=community.id,
        author_id=principal.user.id,
        kind=body.kind,
        title=title,
        body=text_body,
        url=url,
        flair=flair,
        state="visible",
        upvotes=0,
        downvotes=0,
        score=0,
        hot_rank=hot_rank(0, now),
        controversy=0.0,
        comment_count=0,
        created_at=now,
    )
    db.add(post)
    db.flush()
    view = post_views(db, [post], principal.user.id)[0]
    idempotency.finish(db, principal.user.id, idempotency_key, 201, view)
    db.commit()
    return view


@router.get("/v1/posts/{post_id}", response_model=PostSchema)
def read_post(
    post_id: uuid.UUID, principal: Principal | None = Depends(optional_principal), db: Session = Depends(get_db)
) -> PostSchema:
    post = get_post(db, post_id)
    return post_views(db, [post], principal.user.id if principal else None)[0]


@router.patch("/v1/posts/{post_id}", response_model=PostSchema)
def edit_post(
    post_id: uuid.UUID,
    body: UpdatePostRequest,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> PostSchema:
    post = get_post(db, post_id, lock=True)
    if post.state != "visible":
        raise conflict("post_unavailable", "This post has been deleted or removed")
    is_author = post.author_id == principal.user.id
    if body.body is not None:
        if not is_author:
            raise forbidden("Only the author can edit this post")
        if post.kind != "text":
            raise invalid("Only text posts have an editable body", "body")
        post.body = clean_text(body.body, field="body", max_len=40000) or None
        post.edited_at = datetime.now(UTC)
    if body.flair is not None:
        if not (is_author or is_moderator(db, principal.user, post.community_id)):
            raise forbidden("Only the author or a moderator can change flair")
        post.flair = clean_text(body.flair, field="flair", max_len=64, multiline=False) or None
    db.commit()
    return post_views(db, [post], principal.user.id)[0]


@router.delete("/v1/posts/{post_id}", status_code=204)
def delete_post(
    post_id: uuid.UUID,
    reason: str | None = Query(default=None, max_length=500),
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> Response:
    """Author: soft delete (state=deleted). Community moderator/admin: removal (state=removed, audited)."""
    post = get_post(db, post_id, lock=True)
    if post.author_id == principal.user.id:
        if post.state == "visible":
            post.state = "deleted"
            post.edited_at = datetime.now(UTC)
    elif is_moderator(db, principal.user, post.community_id):
        if post.state == "visible":
            post.state = "removed"
            db.add(
                ModerationAction(
                    id=uuid.uuid4(),
                    actor_id=principal.user.id,
                    community_id=post.community_id,
                    action="remove_post",
                    target_type="post",
                    target_id=post.id,
                    reason=clean_text(reason, field="reason", max_len=500) or None,
                    appeal_status="none",
                )
            )
    else:
        raise forbidden("Only the author or a moderator can delete this post")
    db.commit()
    return Response(status_code=204)
