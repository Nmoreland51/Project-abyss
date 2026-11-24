# Threat model (Phase 1 scope)

Scope: Android client ↔ HTTPS/HTTP ↔ FastAPI ↔ PostgreSQL, private pilot. Assets: account
credentials and session tokens; integrity of posts/comments/votes/karma; moderator powers; private
data (none collected beyond handle/password hash/optional display name/bio); availability.

| # | Threat | Where | Mitigation in place | Verified by | Residual / next |
|---|---|---|---|---|---|
| 1 | Credential theft from DB | users, sessions | Argon2id hashes; tokens stored as SHA-256 digests only | `test_credentials_are_not_stored_in_plaintext` | Backups must be encrypted (Phase 6) |
| 2 | Credential stuffing / brute force | /auth/login, /register | 20 req/min per IP and per handle; uniform error; dummy-hash timing | `test_login_failures_do_not_reveal…`, limiter unit test | In-process limiter is single-node; add reverse-proxy limits before public use |
| 3 | Account enumeration | login, register | Same 401 for unknown user and wrong password | test above | Register reveals "handle taken" (inherent to public handles) |
| 4 | Stolen refresh token | /auth/refresh | Rotation on every refresh; reuse after 30 s revokes the session | `test_refresh_reuse_after_grace_revokes_session` | 30 s grace window (ADR-0002) |
| 5 | Token sniffing on network | transport | Release build: HTTPS only. Pilot build: http:// allowed with visible warning | manual review; `network_security_config` | **OD-03**: pilot over http:// is readable on the LAN |
| 6 | Token theft on device | Android storage | AES-256-GCM with non-exportable Keystore key; excluded from backup/device transfer | code review; real-device check pending | Debuggable pilot build allows `run-as` access on the device |
| 7 | Broken object-level authorization | edit/delete/mod routes | Server-side ownership/role checks on every write | `test_cross_account_writes_are_rejected…`, `test_role_checks`, `test_moderation_is_scoped…` | Admin role has no UI and no assignment path yet |
| 8 | SQL injection | all queries | SQLAlchemy bound parameters only; LIKE wildcards escaped; cursors type-validated | `test_injection_strings_are_inert`, `test_tampered_or_mismatched_cursor_is_rejected` | — |
| 9 | Stored XSS / markup | post/comment text | Server stores text, never renders HTML; JSON + `nosniff`; app renders plain `Text` | `test_markup_is_stored_as_text_not_rendered` | Markdown rendering (Phase 2) must use a sanitising renderer |
| 10 | Malicious links | link posts | Only http/https, no embedded credentials, no control chars; opened only on tap in system browser | `test_link_post_validation` | No link reputation checks |
| 11 | SSRF | server | Server never fetches user-supplied URLs | code review | Keep this invariant when adding previews/thumbnails (Phase 5) |
| 12 | Vote/karma manipulation via races or retries | votes | Row lock per target; composite PK; state-setting PUT; reconciler | `test_concurrent_votes_from_many_users_and_retry_storms` | Sock-puppet accounts (Phase 5 abuse controls) |
| 13 | Duplicate posts/comments from retries | create endpoints | Idempotency-Key in same transaction; concurrent replay blocks then replays | `test_idempotent_post_creation`, `test_idempotent_comment_under_concurrent_retries` | Keys never expire yet (cleanup job in Phase 4 worker) |
| 14 | Oversized payloads / DoS | API | 256 KiB Content-Length cap; field length limits; bounded tree reads (500 rows, depth ≤ 15, nesting ≤ 100) | `test_oversized_body_is_rejected`, deep-thread test | Chunked bodies without Content-Length rely on field limits; add proxy body limit |
| 15 | Privilege of the app's DB connection | PostgreSQL | Runtime role has DML only; migrations use a separate owner role | `test_runtime_role_cannot_run_ddl`, clean-boot privilege check | Separate read-only role for analytics later |
| 16 | Secrets in logs | logging | Access log records method/path/status/duration only (no query, headers, bodies) | code review | Add log redaction tests in Phase 6 |
| 17 | Removed content leaking | API responses | Redaction applied server-side for every caller; excluded from feeds | `test_edit_and_delete_permissions` | Search index & caches (Phases 2/4) must inherit removal state |
| 18 | Supply chain | dependencies | Exact pins; `pip-audit` clean on 2026-11-24; Gradle wrapper SHA-256 pinned | evidence/raw/phase1-backend-tests.txt | Add Gradle dependency verification + license scan (Phase 6) |
| 19 | Pilot signing key misuse | APK updates | Clearly labelled pilot key; release key never in repo | — | **OD-04**: anyone can sign a "pilot" update; never distribute pilot builds publicly |
| 20 | Impersonation of historical authors | data model | DB CHECK prevents local author + source record on one row; no credentials for source authors | schema (ADR-0004) | Phase 3 tests T09/T12 |

Out of scope for Phase 1 (tracked): media uploads, reporting/appeals, account deletion/export,
notifications, search, admin tooling, TLS termination, backups.
