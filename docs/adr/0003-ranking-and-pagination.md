# ADR-0003 Ranking formulas and feed pagination

Status: accepted (Phase 1) · Date: 2026-11-24 · Formula versions: `hot-v1`, `controversy-v1`

These are this platform's own published formulas. They are not claimed to reproduce any other
service's ranking. Any change needs a new version string, an owner decision (OD-10) and a note in
release notes. The API returns `ranking_version` with every feed page.

## Formulas (`server/app/ranking.py`)
- **new:** `created_at DESC, id DESC`.
- **top:** `score DESC, id DESC`, restricted to the time window `t ∈ {hour, day, week, month, year, all}`
  (`month` = 30 days, `year` = 365 days) measured back from the page snapshot time.
- **hot-v1:** `sign(score) · log10(max(|score|, 1)) + (created_at − 2026-01-01T00:00Z) / 45000 s`,
  rounded to 7 decimals. One order of magnitude of score ≈ 12.5 hours of age. Score 1 adds nothing.
- **controversy-v1:** `(up + down) ^ (min(up, down) / max(up, down))` when both > 0, else 0.
  Filtered by time window like top.
- **score** = upvotes − downvotes (database CHECK constraint). Imported historical scores (Phase 3)
  are metadata only and never enter these formulas.

`hot_rank` and `controversy` are stored columns recomputed inside the vote transaction, so every
sort uses a partial index `(rank DESC, id DESC) WHERE state = 'visible'`.

## Pagination
Keyset cursors (opaque base64 JSON) carry `{kind, last sort value, last id, as_of}`:
- The cursor is bound to sort, window and scope; a mismatched or tampered cursor → 422.
- `as_of` (time of the first page) excludes posts created after the first page, so new posts never
  shift later pages.
- **Consistency trade-off:** scores can change between page requests. A post whose rank *rises* past
  the cursor is not shown again (already-seen region); a post whose rank *falls* past the cursor can
  appear twice. The client de-duplicates by id. With static data (the T06 fixtures) pagination is
  exactly duplicate- and gap-free, which the tests assert for all four sorts.
- Comments: top-level comments are keyset-paged (`top`: score, `new`/`old`: time); each page includes
  descendants down to `depth` levels (default 8, max 15) and at most 500 rows, filled breadth-first.
  Nodes whose children were cut off report `more_replies`; `GET /v1/comments/{id}` continues the
  thread. Nesting deeper than 100 levels is rejected.

## Pinned posts
Not implemented in Phase 1 (R07 is a Phase 2 requirement); will be an explicit moderator action with
a separate `pinned_at` column, shown above ranked results, never mixed into rank values.
