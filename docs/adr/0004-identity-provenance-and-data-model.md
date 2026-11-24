# ADR-0004 Identity separation, provenance and data-model invariants

Status: accepted (Phase 1 schema; importer is Phase 3) · Date: 2026-11-24

Invariants enforced by the database, not only the API:
- `posts.author_id` and `posts.source_record_id` can never both be set
  (`ck_posts_author_model`; same for comments). A historical record can never be attributed to a
  local account, and `source_records` has no relation to `users` or `sessions` — no credentials can
  exist for an archived author.
- `score = upvotes − downvotes` on posts and comments (`CHECK`), counters non-negative.
- One vote per (user, target): composite primary keys on `post_votes` / `comment_votes`; value ∈ {−1, 1};
  neutral deletes the row.
- A comment's parent must be in the same post: composite FK `(parent_id, post_id) → comments(id, post_id)`.
  Root comments have depth 0, replies depth > 0, no self-parent. Parents are immutable, so cycles
  cannot form.
- Unique normalised handles and community slugs; slug format checked in SQL.
- `source_records (provider, external_id)` unique — the basis for idempotent Phase 3 re-imports.

Response-level visibility: `deleted`/`removed` posts and comments are redacted server-side (author,
title, body, URL hidden) and excluded from feeds; the API never returns removed text to any caller.

Karma: `users.post_karma`/`comment_karma` change by the vote delta in the same transaction as the vote,
excluding self-votes. The test suite includes a reconciler query that recomputes counters and karma
from vote rows and asserts zero drift after concurrent load.
