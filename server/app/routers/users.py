from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..errors import not_found
from ..models import User
from ..schemas import PublicProfile
from ..text import normalize_handle

router = APIRouter(tags=["users"])


@router.get("/v1/users/{handle}", response_model=PublicProfile)
def profile(handle: str, db: Session = Depends(get_db)) -> PublicProfile:
    user = db.scalar(select(User).where(User.handle_norm == normalize_handle(handle), User.status == "active"))
    if user is None:
        raise not_found("User")
    return PublicProfile(
        id=user.id,
        handle=user.handle,
        display_name=user.display_name,
        bio=user.bio,
        post_karma=user.post_karma,
        comment_karma=user.comment_karma,
        created_at=user.created_at,
    )
