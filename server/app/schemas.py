"""Public API contract (request/response models). Published as contracts/openapi.json."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PostSort = Literal["hot", "new", "top", "controversial"]
TimeWindow = Literal["hour", "day", "week", "month", "year", "all"]
CommentSort = Literal["top", "new", "old"]
VoteValue = Literal[-1, 0, 1]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------- auth ----------
class RegisterRequest(_Model):
    handle: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=512)


class LoginRequest(_Model):
    handle: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=512)


class RefreshRequest(_Model):
    refresh_token: str = Field(min_length=1, max_length=200)


class TokenPair(BaseModel):
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime
    token_type: Literal["Bearer"] = "Bearer"
    session_id: uuid.UUID


class UserRef(BaseModel):
    id: uuid.UUID
    handle: str


class Me(BaseModel):
    id: uuid.UUID
    handle: str
    display_name: str | None
    bio: str | None
    post_karma: int
    comment_karma: int
    created_at: datetime
    is_admin: bool


class AuthResponse(BaseModel):
    user: Me
    tokens: TokenPair


class UpdateMeRequest(_Model):
    display_name: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=2000)


class SessionInfo(BaseModel):
    id: uuid.UUID
    created_at: datetime
    last_used_at: datetime
    user_agent: str | None
    current: bool


class PublicProfile(BaseModel):
    id: uuid.UUID
    handle: str
    display_name: str | None
    bio: str | None
    post_karma: int
    comment_karma: int
    created_at: datetime


# ---------- communities ----------
class CommunityRule(_Model):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class CreateCommunityRequest(_Model):
    slug: str = Field(min_length=1, max_length=40)
    display_name: str | None = Field(default=None, max_length=200)
    description: str = Field(default="", max_length=10000)
    rules: list[CommunityRule] = Field(default_factory=list, max_length=15)


class UpdateCommunityRequest(_Model):
    display_name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    rules: list[CommunityRule] | None = Field(default=None, max_length=15)


class MembershipInfo(BaseModel):
    subscribed: bool
    role: Literal["member", "moderator", "owner"]


class Community(BaseModel):
    id: uuid.UUID
    slug: str
    display_name: str
    description: str
    rules: list[CommunityRule]
    subscriber_count: int
    created_at: datetime
    membership: MembershipInfo | None = None


class CommunityRef(BaseModel):
    id: uuid.UUID
    slug: str
    display_name: str


class CommunityPage(BaseModel):
    items: list[Community]
    next_cursor: str | None


class Moderator(BaseModel):
    user: UserRef
    role: Literal["moderator", "owner"]


# ---------- posts ----------
class CreatePostRequest(_Model):
    community: str = Field(min_length=1, max_length=40, description="Community slug")
    kind: Literal["text", "link"] = "text"
    title: str = Field(min_length=1, max_length=600)
    body: str | None = Field(default=None, max_length=80000)
    url: str | None = Field(default=None, max_length=4096)
    flair: str | None = Field(default=None, max_length=128)


class UpdatePostRequest(_Model):
    body: str | None = Field(default=None, max_length=80000)
    flair: str | None = Field(default=None, max_length=128)


class Post(BaseModel):
    id: uuid.UUID
    community: CommunityRef
    author: UserRef | None
    origin: Literal["local", "historical"]
    kind: Literal["text", "link"]
    title: str
    body: str | None
    url: str | None
    url_domain: str | None
    flair: str | None
    state: Literal["visible", "deleted", "removed"]
    score: int
    comment_count: int
    created_at: datetime
    edited_at: datetime | None
    my_vote: VoteValue = 0
    permalink: str


class PostPage(BaseModel):
    items: list[Post]
    next_cursor: str | None
    sort: PostSort
    time_window: TimeWindow
    scope: str
    ranking_version: str


# ---------- comments ----------
class CreateCommentRequest(_Model):
    body: str = Field(min_length=1, max_length=20000)
    parent_id: uuid.UUID | None = None


class UpdateCommentRequest(_Model):
    body: str = Field(min_length=1, max_length=20000)


class CommentNode(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    parent_id: uuid.UUID | None
    author: UserRef | None
    body: str | None
    depth: int
    state: Literal["visible", "deleted", "removed"]
    score: int
    reply_count: int
    created_at: datetime
    edited_at: datetime | None
    my_vote: VoteValue = 0
    replies: list["CommentNode"] = Field(default_factory=list)
    more_replies: int = Field(0, description="Direct replies not included because of depth/size limits")


class CommentPage(BaseModel):
    items: list[CommentNode]
    next_cursor: str | None
    sort: CommentSort


# ---------- votes ----------
class VoteRequest(_Model):
    value: VoteValue


class VoteResult(BaseModel):
    target_id: uuid.UUID
    score: int
    my_vote: VoteValue


class UserContentPage(BaseModel):
    posts: list[Post]
    next_cursor: str | None


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str
    details: list[dict] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class Health(BaseModel):
    status: str
    checks: dict[str, str] = Field(default_factory=dict)
