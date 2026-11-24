"""Votes (R06). PUT sets state (-1, 0, 1) so retries are naturally idempotent.

Concurrency: the target row is locked (SELECT ... FOR UPDATE) for the whole transaction, so
concurrent votes on the same target serialise and counters stay equal to the vote rows.
Karma: the author's karma changes by the vote delta, except for self-votes (not counted)."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..deps import Principal, require_principal
from ..errors import conflict
from ..models import CommentVote, PostVote, User
from ..ranking import controversy, hot_rank
from ..ratelimit import limiter
from ..schemas import VoteRequest, VoteResult
from ..views import get_post
from .comments import _get_comment

router = APIRouter(tags=["votes"])


def _deltas(old: int, new: int) -> tuple[int, int]:
    return int(new == 1) - int(old == 1), int(new == -1) - int(old == -1)


@router.put("/v1/posts/{post_id}/vote", response_model=VoteResult)
def vote_post(
    post_id: uuid.UUID,
    body: VoteRequest,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> VoteResult:
    limiter.check(f"vote:{principal.user.id}", get_settings().write_rate_limit_per_minute * 3)
    post = get_post(db, post_id, lock=True)
    if post.state != "visible":
        raise conflict("post_unavailable", "This post has been deleted or removed")
    uid = principal.user.id
    existing = db.get(PostVote, (uid, post.id), populate_existing=True)
    old = existing.value if existing else 0
    if old != body.value:
        du, dd = _deltas(old, body.value)
        if body.value == 0:
            db.execute(delete(PostVote).where(PostVote.user_id == uid, PostVote.post_id == post.id))
        elif existing:
            existing.value = body.value
        else:
            db.add(PostVote(user_id=uid, post_id=post.id, value=body.value))
        post.upvotes += du
        post.downvotes += dd
        post.score = post.upvotes - post.downvotes
        post.hot_rank = hot_rank(post.score, post.created_at)
        post.controversy = controversy(post.upvotes, post.downvotes)
        if post.author_id is not None and post.author_id != uid:
            db.execute(
                update(User).where(User.id == post.author_id).values(post_karma=User.post_karma + (body.value - old))
            )
        db.commit()
    return VoteResult(target_id=post.id, score=post.score, my_vote=body.value)


@router.put("/v1/comments/{comment_id}/vote", response_model=VoteResult)
def vote_comment(
    comment_id: uuid.UUID,
    body: VoteRequest,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> VoteResult:
    limiter.check(f"vote:{principal.user.id}", get_settings().write_rate_limit_per_minute * 3)
    comment = _get_comment(db, comment_id, lock=True)
    if comment.state != "visible":
        raise conflict("comment_unavailable", "This comment has been deleted or removed")
    uid = principal.user.id
    existing = db.get(CommentVote, (uid, comment.id), populate_existing=True)
    old = existing.value if existing else 0
    if old != body.value:
        du, dd = _deltas(old, body.value)
        if body.value == 0:
            db.execute(delete(CommentVote).where(CommentVote.user_id == uid, CommentVote.comment_id == comment.id))
        elif existing:
            existing.value = body.value
        else:
            db.add(CommentVote(user_id=uid, comment_id=comment.id, value=body.value))
        comment.upvotes += du
        comment.downvotes += dd
        comment.score = comment.upvotes - comment.downvotes
        if comment.author_id is not None and comment.author_id != uid:
            db.execute(
                update(User)
                .where(User.id == comment.author_id)
                .values(comment_karma=User.comment_karma + (body.value - old))
            )
        db.commit()
    return VoteResult(target_id=comment.id, score=comment.score, my_vote=body.value)
