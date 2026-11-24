"""Threaded comments (R05): parent validation, bounded tree reads, edit/delete."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy import literal, select, tuple_, update
from sqlalchemy.orm import Session

from .. import cursor as cur
from .. import idempotency
from ..config import get_settings
from ..db import get_db
from ..deps import Principal, optional_principal, require_principal
from ..errors import conflict, forbidden, invalid, not_found
from ..models import Comment, Community, ModerationAction, Post
from ..ratelimit import limiter
from ..schemas import CommentNode, CommentPage, CommentSort, CreateCommentRequest, UpdateCommentRequest
from ..text import clean_text
from ..views import comment_node, comment_votes_for, get_post, is_moderator, users_for

router = APIRouter(tags=["comments"])

MAX_DEPTH = 100  # hard limit on nesting; deeper replies are rejected
MAX_TREE_ROWS = 500  # bound on descendants returned per request
DEFAULT_TREE_DEPTH = 8


def _sort_key(sort: CommentSort):
    if sort == "new":
        return lambda c: (-c.created_at.timestamp(), str(c.id))
    if sort == "old":
        return lambda c: (c.created_at.timestamp(), str(c.id))
    return lambda c: (-c.score, -c.created_at.timestamp(), str(c.id))


def _build_forest(
    db: Session, roots: list[Comment], *, sort: CommentSort, depth: int, viewer: uuid.UUID | None
) -> list[CommentNode]:
    """Attach descendants of `roots` down to `depth` extra levels, capped at MAX_TREE_ROWS rows."""
    descendants: list[Comment] = []
    if roots and depth > 0:
        tree = (
            select(Comment.id, literal(1).label("lvl"))
            .where(Comment.parent_id.in_([r.id for r in roots]))
            .cte("tree", recursive=True)
        )
        tree = tree.union_all(
            select(Comment.id, (tree.c.lvl + 1).label("lvl")).where(Comment.parent_id == tree.c.id, tree.c.lvl < depth)
        )
        descendants = list(
            db.scalars(
                select(Comment)
                .join(tree, Comment.id == tree.c.id)
                .order_by(tree.c.lvl, Comment.score.desc(), Comment.created_at, Comment.id)
                .limit(MAX_TREE_ROWS)
            ).all()
        )
    everything = roots + descendants
    users = users_for(db, (c.author_id for c in everything))
    votes = comment_votes_for(db, viewer, [c.id for c in everything])
    nodes = {c.id: comment_node(c, users, votes) for c in everything}
    children: dict[uuid.UUID, list[Comment]] = {}
    for c in descendants:
        children.setdefault(c.parent_id, []).append(c)
    key = _sort_key(sort)
    for parent_id, kids in children.items():
        kids.sort(key=key)
        nodes[parent_id].replies = [nodes[k.id] for k in kids]
    for node in nodes.values():
        node.more_replies = max(0, node.reply_count - len(node.replies))
    return [nodes[r.id] for r in roots]


@router.get("/v1/posts/{post_id}/comments", response_model=CommentPage)
def list_comments(
    post_id: uuid.UUID,
    sort: CommentSort = "top",
    cursor: str | None = Query(default=None, max_length=512),
    limit: int = Query(default=20, ge=1, le=100, description="Top-level comments per page"),
    depth: int = Query(default=DEFAULT_TREE_DEPTH, ge=0, le=15, description="Reply levels to include"),
    principal: Principal | None = Depends(optional_principal),
    db: Session = Depends(get_db),
) -> CommentPage:
    post = get_post(db, post_id)
    stmt = select(Comment).where(Comment.post_id == post.id, Comment.parent_id.is_(None))
    kind = f"comments:{post.id}:{sort}"
    c = cur.decode(cursor, kind)
    if sort == "top":
        order = (Comment.score.desc(), Comment.id.desc())
        if c:
            if not isinstance(c.get("v"), int):
                raise invalid("Invalid or expired cursor", "cursor")
            stmt = stmt.where(tuple_(Comment.score, Comment.id) < tuple_(c["v"], uuid.UUID(c["id"])))
    else:
        asc = sort == "old"
        order = (Comment.created_at.asc(), Comment.id.asc()) if asc else (Comment.created_at.desc(), Comment.id.desc())
        if c:
            try:
                at = datetime.fromisoformat(c["v"])
            except (TypeError, ValueError, KeyError) as exc:
                raise invalid("Invalid or expired cursor", "cursor") from exc
            pair, bound = tuple_(Comment.created_at, Comment.id), tuple_(at, uuid.UUID(c["id"]))
            stmt = stmt.where(pair > bound if asc else pair < bound)
    roots = list(db.scalars(stmt.order_by(*order).limit(limit + 1)).all())
    more = len(roots) > limit
    roots = roots[:limit]
    next_cursor = None
    if more:
        tail = roots[-1]
        v = tail.score if sort == "top" else tail.created_at.isoformat()
        next_cursor = cur.encode({"k": kind, "v": v, "id": str(tail.id)})
    viewer = principal.user.id if principal else None
    items = _build_forest(db, roots, sort=sort, depth=depth, viewer=viewer)
    return CommentPage(items=items, next_cursor=next_cursor, sort=sort)


@router.get("/v1/comments/{comment_id}", response_model=CommentNode)
def comment_thread(
    comment_id: uuid.UUID,
    sort: CommentSort = "top",
    depth: int = Query(default=DEFAULT_TREE_DEPTH, ge=0, le=15),
    principal: Principal | None = Depends(optional_principal),
    db: Session = Depends(get_db),
) -> CommentNode:
    """A single comment with its subtree ("continue this thread")."""
    comment = _get_comment(db, comment_id)
    viewer = principal.user.id if principal else None
    return _build_forest(db, [comment], sort=sort, depth=depth, viewer=viewer)[0]


def _get_comment(db: Session, comment_id: uuid.UUID, *, lock: bool = False) -> Comment:
    stmt = (
        select(Comment)
        .join(Post, Post.id == Comment.post_id)
        .join(Community, Community.id == Post.community_id)
        .where(Comment.id == comment_id, Community.status == "active")
    )
    if lock:
        stmt = stmt.with_for_update(of=Comment)
    comment = db.scalar(stmt)
    if comment is None:
        raise not_found("Comment")
    return comment


@router.post("/v1/posts/{post_id}/comments", response_model=CommentNode, status_code=201)
def create_comment(
    post_id: uuid.UUID,
    body: CreateCommentRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
):
    limiter.check(f"write:{principal.user.id}", get_settings().write_rate_limit_per_minute)
    payload = {"post_id": str(post_id), **body.model_dump()}
    replay = idempotency.begin(db, principal.user.id, idempotency_key, "create_comment", payload)
    if replay is not None:
        return replay
    post = get_post(db, post_id)
    if post.state != "visible":
        raise conflict("post_unavailable", "This post has been deleted or removed")
    text = clean_text(body.body, field="body", max_len=10000, min_len=1)
    depth = 0
    if body.parent_id is not None:
        parent = db.scalar(select(Comment).where(Comment.id == body.parent_id, Comment.post_id == post.id))
        if parent is None:
            raise invalid("Parent comment does not exist in this post", "parent_id")
        if parent.state != "visible":
            raise conflict("parent_unavailable", "You cannot reply to a deleted or removed comment")
        depth = parent.depth + 1
        if depth > MAX_DEPTH:
            raise invalid(f"Threads cannot nest deeper than {MAX_DEPTH} levels", "parent_id")
    now = datetime.now(UTC)
    comment = Comment(
        id=uuid.uuid4(),
        post_id=post.id,
        parent_id=body.parent_id,
        author_id=principal.user.id,
        body=text,
        depth=depth,
        state="visible",
        upvotes=0,
        downvotes=0,
        score=0,
        reply_count=0,
        created_at=now,
    )
    db.add(comment)
    db.flush()
    if body.parent_id is not None:
        db.execute(update(Comment).where(Comment.id == body.parent_id).values(reply_count=Comment.reply_count + 1))
    db.execute(update(Post).where(Post.id == post.id).values(comment_count=Post.comment_count + 1))
    users = users_for(db, [principal.user.id])
    view = comment_node(comment, users, {})
    idempotency.finish(db, principal.user.id, idempotency_key, 201, view)
    db.commit()
    return view


@router.patch("/v1/comments/{comment_id}", response_model=CommentNode)
def edit_comment(
    comment_id: uuid.UUID,
    body: UpdateCommentRequest,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> CommentNode:
    comment = _get_comment(db, comment_id, lock=True)
    if comment.author_id != principal.user.id:
        raise forbidden("Only the author can edit this comment")
    if comment.state != "visible":
        raise conflict("comment_unavailable", "This comment has been deleted or removed")
    comment.body = clean_text(body.body, field="body", max_len=10000, min_len=1)
    comment.edited_at = datetime.now(UTC)
    db.commit()
    users = users_for(db, [principal.user.id])
    return comment_node(comment, users, comment_votes_for(db, principal.user.id, [comment.id]))


@router.delete("/v1/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: uuid.UUID,
    reason: str | None = Query(default=None, max_length=500),
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> Response:
    comment = _get_comment(db, comment_id, lock=True)
    post = db.get(Post, comment.post_id)
    assert post is not None
    if comment.author_id == principal.user.id:
        if comment.state == "visible":
            comment.state = "deleted"
            comment.edited_at = datetime.now(UTC)
    elif is_moderator(db, principal.user, post.community_id):
        if comment.state == "visible":
            comment.state = "removed"
            db.add(
                ModerationAction(
                    id=uuid.uuid4(),
                    actor_id=principal.user.id,
                    community_id=post.community_id,
                    action="remove_comment",
                    target_type="comment",
                    target_id=comment.id,
                    reason=clean_text(reason, field="reason", max_len=500) or None,
                    appeal_status="none",
                )
            )
    else:
        raise forbidden("Only the author or a moderator can delete this comment")
    db.commit()
    return Response(status_code=204)
