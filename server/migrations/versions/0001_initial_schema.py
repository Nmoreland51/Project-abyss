"""Initial live-platform schema (Phase 1).

Revision ID: 0001
Revises:
Create Date: 2026-11-24
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


UPGRADE_SQL = r"""
CREATE TABLE users (
    id              uuid PRIMARY KEY,
    handle          varchar(20) NOT NULL,
    handle_norm     varchar(20) NOT NULL UNIQUE,
    password_hash   text NOT NULL,
    status          varchar(16) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'suspended', 'deleted')),
    is_admin        boolean NOT NULL DEFAULT false,
    display_name    varchar(50),
    bio             varchar(500),
    post_karma      bigint NOT NULL DEFAULT 0,
    comment_karma   bigint NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CHECK (handle_norm = lower(handle_norm))
);

CREATE TABLE sessions (
    id                  uuid PRIMARY KEY,
    user_id             uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_hash         varchar(64) NOT NULL UNIQUE,
    access_expires_at   timestamptz NOT NULL,
    refresh_hash        varchar(64) NOT NULL UNIQUE,
    refresh_expires_at  timestamptz NOT NULL,
    prev_refresh_hash   varchar(64),
    rotated_at          timestamptz NOT NULL DEFAULT now(),
    user_agent          varchar(200),
    created_at          timestamptz NOT NULL DEFAULT now(),
    last_used_at        timestamptz NOT NULL DEFAULT now(),
    revoked_at          timestamptz,
    revoked_reason      varchar(32)
);
CREATE INDEX ix_sessions_user ON sessions (user_id);
CREATE INDEX ix_sessions_prev_refresh ON sessions (prev_refresh_hash) WHERE prev_refresh_hash IS NOT NULL;

CREATE TABLE communities (
    id                uuid PRIMARY KEY,
    slug              varchar(21) NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_]{3,21}$'),
    display_name      varchar(100) NOT NULL,
    description       text NOT NULL DEFAULT '',
    rules             jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_by        uuid REFERENCES users(id) ON DELETE SET NULL,
    status            varchar(16) NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active', 'archived', 'banned')),
    subscriber_count  integer NOT NULL DEFAULT 0 CHECK (subscriber_count >= 0),
    created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_communities_popular ON communities (subscriber_count DESC, id DESC);

CREATE TABLE memberships (
    user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    community_id  uuid NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    role          varchar(16) NOT NULL DEFAULT 'member'
                  CHECK (role IN ('member', 'moderator', 'owner')),
    subscribed    boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, community_id)
);
CREATE INDEX ix_memberships_community_role ON memberships (community_id, role);

-- Historical provenance (populated only by the Phase 3 importer after a recorded rights decision).
CREATE TABLE source_records (
    id                     uuid PRIMARY KEY,
    provider               varchar(64) NOT NULL,
    external_id            varchar(128) NOT NULL,
    canonical_url          text,
    original_author_label  varchar(128),
    source_created_at      timestamptz,
    captured_at            timestamptz,
    imported_at            timestamptz NOT NULL DEFAULT now(),
    digest                 varchar(64) NOT NULL,
    rights_status          varchar(32) NOT NULL DEFAULT 'unresolved',
    historical_score       integer,
    removal_state          varchar(16) NOT NULL DEFAULT 'none',
    UNIQUE (provider, external_id)
);

CREATE TABLE posts (
    id                uuid PRIMARY KEY,
    community_id      uuid NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    author_id         uuid REFERENCES users(id) ON DELETE SET NULL,
    source_record_id  uuid REFERENCES source_records(id),
    kind              varchar(8) NOT NULL CHECK (kind IN ('text', 'link')),
    title             varchar(300) NOT NULL CHECK (length(title) > 0),
    body              text,
    url               text,
    flair             varchar(64),
    state             varchar(16) NOT NULL DEFAULT 'visible'
                      CHECK (state IN ('visible', 'deleted', 'removed')),
    upvotes           integer NOT NULL DEFAULT 0 CHECK (upvotes >= 0),
    downvotes         integer NOT NULL DEFAULT 0 CHECK (downvotes >= 0),
    score             integer NOT NULL DEFAULT 0,
    hot_rank          double precision NOT NULL DEFAULT 0,
    controversy       double precision NOT NULL DEFAULT 0,
    comment_count     integer NOT NULL DEFAULT 0 CHECK (comment_count >= 0),
    created_at        timestamptz NOT NULL DEFAULT now(),
    imported_at       timestamptz,
    edited_at         timestamptz,
    -- Historical records are never attributed to a local account.
    CONSTRAINT ck_posts_author_model CHECK (author_id IS NULL OR source_record_id IS NULL),
    CONSTRAINT ck_posts_score CHECK (score = upvotes - downvotes),
    CONSTRAINT ck_posts_link_has_url CHECK (kind <> 'link' OR url IS NOT NULL OR state <> 'visible')
);
CREATE INDEX ix_posts_new ON posts (created_at DESC, id DESC) WHERE state = 'visible';
CREATE INDEX ix_posts_hot ON posts (hot_rank DESC, id DESC) WHERE state = 'visible';
CREATE INDEX ix_posts_top ON posts (score DESC, id DESC) WHERE state = 'visible';
CREATE INDEX ix_posts_controversial ON posts (controversy DESC, id DESC) WHERE state = 'visible';
CREATE INDEX ix_posts_community_new ON posts (community_id, created_at DESC, id DESC) WHERE state = 'visible';
CREATE INDEX ix_posts_community_hot ON posts (community_id, hot_rank DESC, id DESC) WHERE state = 'visible';
CREATE INDEX ix_posts_community_top ON posts (community_id, score DESC, id DESC) WHERE state = 'visible';
CREATE INDEX ix_posts_author ON posts (author_id, created_at DESC);

CREATE TABLE comments (
    id                uuid PRIMARY KEY,
    post_id           uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    parent_id         uuid,
    author_id         uuid REFERENCES users(id) ON DELETE SET NULL,
    source_record_id  uuid REFERENCES source_records(id),
    body              text NOT NULL,
    depth             smallint NOT NULL DEFAULT 0 CHECK (depth >= 0),
    state             varchar(16) NOT NULL DEFAULT 'visible'
                      CHECK (state IN ('visible', 'deleted', 'removed')),
    upvotes           integer NOT NULL DEFAULT 0 CHECK (upvotes >= 0),
    downvotes         integer NOT NULL DEFAULT 0 CHECK (downvotes >= 0),
    score             integer NOT NULL DEFAULT 0,
    reply_count       integer NOT NULL DEFAULT 0 CHECK (reply_count >= 0),
    created_at        timestamptz NOT NULL DEFAULT now(),
    edited_at         timestamptz,
    CONSTRAINT uq_comments_id_post UNIQUE (id, post_id),
    -- A parent must belong to the same post (prevents cross-post parents at the database level).
    CONSTRAINT fk_comments_parent_same_post FOREIGN KEY (parent_id, post_id)
        REFERENCES comments (id, post_id) ON DELETE CASCADE,
    CONSTRAINT ck_comments_not_self_parent CHECK (parent_id IS NULL OR parent_id <> id),
    CONSTRAINT ck_comments_root_depth CHECK ((parent_id IS NULL) = (depth = 0)),
    CONSTRAINT ck_comments_author_model CHECK (author_id IS NULL OR source_record_id IS NULL),
    CONSTRAINT ck_comments_score CHECK (score = upvotes - downvotes)
);
CREATE INDEX ix_comments_post_root ON comments (post_id, created_at, id) WHERE parent_id IS NULL;
CREATE INDEX ix_comments_parent ON comments (parent_id, created_at, id);
CREATE INDEX ix_comments_author ON comments (author_id, created_at DESC);

CREATE TABLE post_votes (
    user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id     uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    value       smallint NOT NULL CHECK (value IN (-1, 1)),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, post_id)
);
CREATE INDEX ix_post_votes_target ON post_votes (post_id);

CREATE TABLE comment_votes (
    user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    comment_id  uuid NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    value       smallint NOT NULL CHECK (value IN (-1, 1)),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, comment_id)
);
CREATE INDEX ix_comment_votes_target ON comment_votes (comment_id);

CREATE TABLE idempotency_keys (
    user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key           varchar(128) NOT NULL,
    endpoint      varchar(64) NOT NULL,
    request_hash  varchar(64) NOT NULL,
    status_code   smallint,
    response      jsonb,
    created_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, key)
);
CREATE INDEX ix_idempotency_created ON idempotency_keys (created_at);

CREATE TABLE moderation_actions (
    id             uuid PRIMARY KEY,
    actor_id       uuid REFERENCES users(id) ON DELETE SET NULL,
    community_id   uuid REFERENCES communities(id) ON DELETE CASCADE,
    action         varchar(32) NOT NULL,
    target_type    varchar(16) NOT NULL,
    target_id      uuid NOT NULL,
    reason         varchar(500),
    appeal_status  varchar(16) NOT NULL DEFAULT 'none',
    created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_mod_actions_community ON moderation_actions (community_id, created_at DESC);
"""

DOWNGRADE_SQL = r"""
DROP TABLE IF EXISTS moderation_actions;
DROP TABLE IF EXISTS idempotency_keys;
DROP TABLE IF EXISTS comment_votes;
DROP TABLE IF EXISTS post_votes;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS source_records;
DROP TABLE IF EXISTS memberships;
DROP TABLE IF EXISTS communities;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS users;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
