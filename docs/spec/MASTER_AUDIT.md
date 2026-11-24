# RetroReddit V2 — Master audit and implementation specification
Revision 2.0 | 2026-11-24 | Status: proposed, not implemented or runtime-verified

## 1. Mission and product boundary
Build a live, independent discussion platform with a native Android client and a compact, classic Reddit-inspired experience. This supersedes the historical time-machine design. Home opens to a normal feed, not a calendar, archive list, or Wayback frame. Historical material is an optional background seed; the product must work with zero archive availability. New users, communities, posts, comments and votes persist on our server. No assumption of access to existing Reddit accounts, private data, current user base, or complete historical content. No claim of official Reddit affiliation. Use a distinct public-facing name and original assets after trademark review; RetroReddit is a working project name.

## 2. Audit findings and decisions
| ID | Finding | Severity | Decision |
|---|---|---|---|
| A01 | Earlier architecture is read-only and archive-centric | Critical | Replace core with independent transactional service |
| A02 | Source code availability is not content republication permission | Critical | Separate code license inventory from per-source content authorization |
| A03 | Historical authors cannot authenticate to independent accounts automatically | High | Separate historical attribution and local identity; no impersonation |
| A04 | Old vote totals are snapshots, not local votes | High | Keep independent counters and label historical values |
| A05 | Archive completeness is unknown | High | Provenance and coverage manifest; never synthesize missing records |
| A06 | A live platform requires trust, abuse controls and removal workflows | Critical | Document operational policy and build moderation before public launch |
| A07 | Mobile device cannot act as reliable shared service | High | Deploy server independently of Android client |
| A08 | Legacy code is archived and may contain obsolete dependencies | High | Use as behavioral reference, modern implementation by default |
| A09 | Real engagement cannot be imported | High | Seed small communities with consenting contributors; never fake activity |
| A10 | Whole-site import creates unbounded storage and rights risk | High | Start with a small authorized dataset; benchmark before scaling |

## 3. Product requirements
R01: Anonymous read of public communities, home and all feeds; authenticated write operations.
R02: Account creation, login, logout, recovery, session revocation, profile and preferences; no password import from Reddit.
R03: Community creation, subscriptions, descriptions, rules, role-based moderator membership.
R04: Text and link posts, with title, author attribution, timestamp, flair and permalink. Add image and video uploads in the media phase.
R05: Nested comments, collapse/expand, replies, edit and delete, stable ordering, pagination for deep threads.
R06: Upvote/downvote/neutral; one state per actor per target; transactional counters; server-derived local karma.
R07: Home subscriptions, all, community listings; new, top, hot, controversial (document versioned formulas); time windows; explicit pinned posts.
R08: Search community names, local posts and permitted imported posts/comments; stable pagination; removal parity across results.
R09: Historical records display in ordinary feeds and search with unobtrusive origin/timestamp metadata. Historical thread replies are local contributions when enabled for authorized imported material. Never rewrite original timestamps or falsely imply authors joined the new platform.
R10: Bookmarks, user-controlled preferences, inbox, notification settings, deep links, block and mute.
R11: Native classic compact interface: title-centric list, small thumbnails, score arrows, comment counts, nested discussion, tabs/drawer; light and dark mode, accessibility and responsive text scaling.
R12: Local read cache, offline bookmarks and explicitly queued idempotent operations with visible pending/failure states. Server is authoritative for shared writes.
R13: Rights-aware archive importer, provenance, deduplication, checkpoints, source health status, dry run, quarantine, replay, removal propagation. Start with synthetic or rights-cleared data; no unauthorized archive mirroring.
R14: Media upload validation, storage quotas, signed upload/download where appropriate, content type validation, safe rendering, moderation and removal. No automatic collection of removed or restricted media; no circumvention of archive controls.
R15: User reports, moderator queue, community roles, admin escalation, audit log, appeal process and public content policy. User preference controls are transparent and separate from legal obligations or platform-wide operational policy. Do not silently add policy changes.
R16: Account/data export, deletion requests, cache/index invalidation, retention schedule, encrypted backups, restoration drills.
R17: Deployment configuration, TLS, migrations, health metrics, structured redacted logs, error monitoring, rollback and incident response.
R18: Signed Android release, versioned API, migration-tested Room schema, end-to-end real-device verification.
R19: Optional Abyss integration through read-only documented API for authorized public information, opt-in and separately deployable; not a launch dependency.

## 4. Historical foundation and integration
Historical import must be a background administrator job, never the main navigation. Use adapters with explicit licenses/terms/permissions review and source registry. Archive availability is not a republication license. If authorization is unclear, retain only permissible reference metadata or links, or leave the record unavailable. Honor applicable removals and restrictions; do not reconstruct content specifically to evade a removal. Preserve original source ID, permalink, original date, capture date (if known), import timestamp, attribution, source digest and permission decision. Import into staging, validate, dedupe and publish approved records. Separate source attribution from local account IDs. Never create login credentials for an archived author. Archived scores are metadata only; local score starts at zero. Missing parent: show documented placeholder; do not invent text. Old posts remain old in New; Top/all-time and ordinary search may surface them. If desired, a clearly labeled historical discovery section can be a secondary feed, never the default time machine. A single database serves normal feed operations.

## 5. Architecture choice
Modern modular monolith: Kotlin/Compose Android + FastAPI/Python backend + PostgreSQL, object storage when needed. PostgreSQL full-text search initially; add external search only after benchmarks justify it. Redis optional for measured queue/cache needs, not baseline. Database transactions for votes and memberships. Separate ingestion worker shares domain contracts but not unrestricted writes. Use Docker Compose for local development; managed database or equivalent backup/monitoring for production. See SYSTEM_ARCHITECTURE.md.

## 6. Content and governance decisions
The goal is classic usability and independent governance, not a promise that all content that once existed can be recovered or hosted. Owner chooses documented community rules and feature defaults within applicable law, rights, and distribution rules. Implement report/block/remove/appeal and administrator accountability. Decide age-sensitive content policy, media previews, community governance and distribution channel before public launch; no hidden additions. For potentially disturbing but lawful content, define explicit labeling and user-controlled presentation settings consistent with selected policy. Do not build tooling aimed at sourcing removed violent material, unlawful abuse material, or unauthorized private data. Test with synthetic media. Separate personal test deployment from public service; public hosting carries additional obligations. See DATA_AND_GOVERNANCE.md.

## 7. Release and performance goals (proposed; measure baseline first)
On specified reference Android device and staging server: p95 cached feed render <=500 ms; p95 warm feed API <=500 ms at 20 concurrent users with 100k synthetic posts; search p95 <=1 s; vote mutation p95 <=500 ms under same load; no duplicate votes after retry; 100% approved import rows have provenance; zero critical security findings; 100% required acceptance tests pass; offline cache remains useful after server outage. Record hardware, dataset, network and workload. No invented benchmark claims. Public launch requires successful backup restore, review of source rights and distribution requirements, and documented moderation capacity.

## 8. Deliverables and phase gates
See DEVELOPMENT_ROADMAP.md and TESTING_STRATEGY.md. Required: installable signed APK, reproducible backend deployment, OpenAPI schema, DB migrations, rights-cleared sample dataset, operator handbook, real-device evidence, test reports, benchmark report, release checklist and known limitations. Each phase ends with audit of changed components, regression suite, commit and documented residual issues. No cosmetic completion: two separate accounts must exchange comments and votes against a real shared backend and survive app/server restarts. Archive outage must not interrupt live participation.

## 9. Sources and verification status
Reference URLs checked for planning; no live endpoint integration or archive import performed. Original code: https://github.com/reddit-archive/reddit (archived 2017); license: https://github.com/reddit-archive/reddit/blob/master/LICENSE ; Arctic Shift: https://github.com/ArthurHeitmann/arctic_shift and https://github.com/ArthurHeitmann/arctic_shift/blob/master/api/README.md ; CDX: https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server ; Android offline-first: https://developer.android.com/topic/architecture/data-layer/offline-first . Revalidate source terms and dependencies at implementation and launch.
