"""Shared query helpers and response serialisation with server-side visibility redaction."""

import uuid
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import schemas
from .errors import not_found
from .models import Comment, CommentVote, Community, Membership, Post, PostVote, User
from .text import url_domain

REDACTED = {"deleted": "[deleted]", "removed": "[removed]"}


def get_active_community(db: Session, slug: str, *, lock: bool = False) -> Community:
    stmt = select(Community).where(Community.slug == slug.strip().lower(), Community.status == "active")
    if lock:
        stmt = stmt.with_for_update()
    community = db.scalar(stmt)
    if community is None:
        raise not_found("Community")
    return community


def membership_of(db: Session, user_id: uuid.UUID | None, community_id: uuid.UUID) -> Membership | None:
    if user_id is None:
        return None
    return db.get(Membership, (user_id, community_id))


def is_moderator(db: Session, user: User, community_id: uuid.UUID) -> bool:
    if user.is_admin:
        return True
    m = membership_of(db, user.id, community_id)
    return m is not None and m.role in ("moderator", "owner")


def community_view(c: Community, m: Membership | None = None) -> schemas.Community:
    return schemas.Community(
        id=c.id,
        slug=c.slug,
        display_name=c.display_name,
        description=c.description,
        rules=[schemas.CommunityRule(**r) for r in (c.rules or [])],
        subscriber_count=c.subscriber_count,
        created_at=c.created_at,
        membership=schemas.MembershipInfo(subscribed=m.subscribed, role=m.role) if m else None,
    )


def _users(db: Session, ids: Iterable[uuid.UUID | None]) -> dict[uuid.UUID, User]:
    wanted = {i for i in ids if i is not None}
    if not wanted:
        return {}
    return {u.id: u for u in db.scalars(select(User).where(User.id.in_(wanted)))}


def _user_ref(u: User | None) -> schemas.UserRef | None:
    if u is None or u.status == "deleted":
        return None
    return schemas.UserRef(id=u.id, handle=u.handle)


def post_views(db: Session, posts: list[Post], viewer_id: uuid.UUID | None) -> list[schemas.Post]:
    if not posts:
        return []
    users = _users(db, (p.author_id for p in posts))
    comms = {c.id: c for c in db.scalars(select(Community).where(Community.id.in_({p.community_id for p in posts})))}
    votes: dict[uuid.UUID, int] = {}
    if viewer_id is not None:
        votes = dict(
            db.execute(
                select(PostVote.post_id, PostVote.value).where(
                    PostVote.user_id == viewer_id, PostVote.post_id.in_([p.id for p in posts])
                )
            ).all()
        )
    out = []
    for p in posts:
        c = comms[p.community_id]
        hidden = p.state != "visible"
        out.append(
            schemas.Post(
                id=p.id,
                community=schemas.CommunityRef(id=c.id, slug=c.slug, display_name=c.display_name),
                author=None if hidden else _user_ref(users.get(p.author_id)),
                origin="historical" if p.source_record_id else "local",
                kind=p.kind,
                title=REDACTED[p.state] if hidden else p.title,
                body=None if hidden else p.body,
                url=None if hidden else p.url,
                url_domain=None if hidden else url_domain(p.url),
                flair=None if hidden else p.flair,
                state=p.state,
                score=p.score,
                comment_count=p.comment_count,
                created_at=p.created_at,
                edited_at=p.edited_at,
                my_vote=votes.get(p.id, 0),
                permalink=f"/c/{c.slug}/p/{p.id}",
            )
        )
    return out


def get_post(db: Session, post_id: uuid.UUID, *, lock: bool = False) -> Post:
    stmt = (
        select(Post)
        .join(Community, Community.id == Post.community_id)
        .where(Post.id == post_id, Community.status == "active")
    )
    if lock:
        stmt = stmt.with_for_update(of=Post)
    post = db.scalar(stmt)
    if post is None:
        raise not_found("Post")
    return post


def comment_votes_for(db: Session, viewer_id: uuid.UUID | None, ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if viewer_id is None or not ids:
        return {}
    return dict(
        db.execute(
            select(CommentVote.comment_id, CommentVote.value).where(
                CommentVote.user_id == viewer_id, CommentVote.comment_id.in_(ids)
            )
        ).all()
    )


def comment_node(c: Comment, users: dict[uuid.UUID, User], votes: dict[uuid.UUID, int]) -> schemas.CommentNode:
    hidden = c.state != "visible"
    return schemas.CommentNode(
        id=c.id,
        post_id=c.post_id,
        parent_id=c.parent_id,
        author=None if hidden else _user_ref(users.get(c.author_id)),
        body=REDACTED[c.state] if hidden else c.body,
        depth=c.depth,
        state=c.state,
        score=c.score,
        reply_count=c.reply_count,
        created_at=c.created_at,
        edited_at=c.edited_at,
        my_vote=votes.get(c.id, 0),
    )


def users_for(db: Session, ids: Iterable[uuid.UUID | None]) -> dict[uuid.UUID, User]:
    return _users(db, ids)
