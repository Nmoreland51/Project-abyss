# System architecture — V2
## Runtime topology
Android (Kotlin, Compose, ViewModel/Flow, Room, WorkManager, HTTP client) -> HTTPS REST /v1 -> FastAPI modular monolith -> PostgreSQL. Backend worker handles notifications and permitted imports via durable database job queue. Object storage for approved uploads with lifecycle management; optional Redis only if measured. Reverse proxy TLS and rate limits. No direct Android-to-archive dependency; optional external link opens browser. Docker Compose for dev/staging. No obsolete Reddit runtime dependencies.

## Repository layout
```
android/app/       # navigation, DI, screens
android/core/      # model, network, database, design system
android/feature/   # feed, threads, community, auth, settings
server/app/        # auth, users, communities, posts, comments, votes, feeds, search, moderation, media, notifications
server/migrations/ # schema migrations
worker/            # ingestion and background jobs
contracts/         # OpenAPI and fixtures
infra/             # compose, deploy, backup/restore
 tests/            # integration, end-to-end, performance
 docs/             # audit, decisions, operations, release evidence
```
## Data model (minimum)
- users(id UUID, handle unique normalized, password_hash or external identity, status, created_at); sessions(token_hash, user_id, expires, revoked_at); profiles(user_id, display fields).
- communities(id, slug unique, display_name, description, rules, created_by, created_at, status); memberships(user_id, community_id, role, subscribed), unique pair; separate moderation grants if needed.
- posts(id, community_id, local_author_id nullable, source_record_id nullable, title, body, link, type, flair, created_at, imported_at, edited_at, state); check author model; historical data never mapped to credentials.
- comments(id, post_id, parent_id nullable, local_author_id nullable, source_record_id nullable, body, created_at, edited_at, state); prevent cross-post parents and cycles; stable cursor indexes.
- post_votes(user_id, post_id, value -1/+1) and comment_votes analog; unique composite keys; neutral removes row. Local scores derived or updated transactionally; reconciler checks aggregates. Karma is derived from local policy, not historical snapshots.
- source_records(id, provider, external_id, canonical_url, original_author_label, source_created_at, captured_at, imported_at, digest, rights_status, historical_score nullable, removal_state); unique provider/external id; source revisions stored separately when appropriate.
- imports(id, adapter, checkpoint, status, counts, manifest_digest); staging_records; removal_tombstones keyed by source IDs to prevent accidental reimport.
- media(id, object_key, mime, size, digest, owner, state); attachments; reports; moderation_actions; appeals; bookmarks; notifications; blocks; audit_events; durable_jobs; idempotency_keys.
- Full-text GIN indexes on approved visible text; composite indexes for community/date, comment parent/date, memberships, vote target, notification recipient. Enforce state constraints in query layer, not just UI.

## API contract (proposed; publish OpenAPI and generate typed Android models)
| Method | Route | Notes |
|---|---|---|
| POST | /v1/auth/register, /login, /refresh, /logout | auth module routes; token rotation |
| GET/PATCH | /v1/me | profile/settings |
| GET | /v1/feed?sort=hot&cursor=... | opaque cursor; optional time window |
| GET/POST | /v1/communities | browse/create |
| GET | /v1/communities/{slug}/posts | stable pagination |
| PUT/DELETE | /v1/communities/{id}/membership | idempotent |
| POST | /v1/posts | auth, idempotency key |
| GET/PATCH/DELETE | /v1/posts/{id} | ownership/mod rights |
| GET/POST | /v1/posts/{id}/comments | parent validation, pagination |
| PATCH/DELETE | /v1/comments/{id} | permissions |
| PUT | /v1/posts/{id}/vote or /v1/comments/{id}/vote | body value -1,0,1 |
| GET | /v1/search?q=...&type=... | visible corpus only |
| PUT/DELETE | /v1/bookmarks/{post_id} | idempotent |
| GET | /v1/notifications | inbox |
| POST | /v1/reports | report target and reason |
| GET/POST | /v1/mod/queue, /v1/mod/actions | scoped role checks |
| POST | /v1/media/uploads | phase 5; upload authorization |
| GET/POST | /v1/me/export, /v1/me/deletion | verified ownership |
| GET | /health/live, /health/ready | separate readiness |
Errors: consistent JSON code/message/request_id; 401 auth, 403 permission, 404 not visible, 409 conflict, 422 validation, 429 rate limit, 503 transient. All routes enforce visibility and authorization server-side. Use UUID local IDs, not source IDs, in normal API. Write endpoints include idempotency strategy; vote PUT is naturally state-setting. API versions additive by default.

## Feed and ranking
New: created_at DESC, id tie-break. Top: local score DESC within selected age window, stable tie-break. Hot initial version: sign(score)*log10(max(abs(score),1)) + created_at_seconds/45000; use a fixed epoch for numeric stability and document formula version; no claim exact Reddit algorithm. Controversial: if both up and down >0, (up+down)^(min(up,down)/max(up,down)); zero otherwise. Pinned posts explicit, separate. Rank snapshot or cursor epoch prevents duplicates when scores change during pagination; document consistency tradeoff. Old imported items do not masquerade as recent. Home subscribed communities; All public eligible communities; filters consistent with visibility. Use pagination and query plans, not unbounded feed reads.

## Android interaction and state
Launch to compact Home; tabs Home/All/Communities/Inbox/Profile or drawer. List row title, source/community, score controls, relative age, comment count, thumbnail and optional provenance marker. Thread displays nested replies, expand/collapse, composer; no recursive unbounded UI. Repository local cache feeds StateFlow; remote fetch updates Room transactionally. Writes require server confirmation or explicit pending queue; WorkManager retries transient failures with capped backoff and idempotency. On auth revocation clear private cache and pending writes. Cache keys include account and query. Accessible controls with content descriptions, text scaling, contrast. Use original icons and distinct branding.

## Import data flow
Source registry -> permission decision -> staging -> validate/normalize -> dedupe -> preview -> publish transaction -> index update -> coverage report. Batch cursor/checkpoint and replay safety; respect source quotas; no access-control bypass. Separate historical author and local identity. Removal job removes visible copies, search index, cache and object references, adds non-content tombstone; backup retention documented. Use authorized dataset only. No archive dependency in request path.

## Security / operations
Argon2id or current reviewed password hashing; short-lived access and rotated refresh tokens; Android Keystore-backed secret storage; TLS; no secrets in logs or APK. Validate Markdown and URLs; no raw untrusted HTML execution. Prevent object-level authorization errors, SQL injection, upload abuse, SSRF (no arbitrary server-side URL fetch by users), enumeration and credential stuffing. Least-privilege DB roles, scoped admin actions and backups. Log request IDs and operational metrics without secrets. Migration rollback strategy, restore drills, dependency/license scanning. See testing and governance files.
