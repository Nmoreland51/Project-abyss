# Status and phase-gate report

Updated 2026-11-24. Evidence files are in `docs/evidence/raw/` (verbatim command output).
Environment for all evidence below: Linux x86_64 cloud container, 4 vCPU, 15 GB RAM, no KVM (so **no
Android emulator**), Docker 29.9.3, PostgreSQL 18.7 (container), Python 3.13.18, JDK 21.0.13.

## Phase 0 — Foundation
| Exit criterion | Result | Evidence |
|---|---|---|
| Repository audit | Greenfield: `Project-abyss` had no commits; nothing to migrate or preserve | `git log` empty at start |
| Platform scope, branding, decisions documented | Done; owner decisions listed with defaults and alternatives | `docs/OWNER_DECISIONS.md`, `docs/adr/0001–0005` |
| Code/data rights, source permission registry | Done; all external sources `unresolved`/`not_used`; no third-party content in repo | `contracts/source_registry.json` |
| Threat model | Done for Phase 1 scope | `docs/THREAT_MODEL.md` |
| Dependency versions | Latest stable checked 2026-11-24; exact pins; `pip-audit`: no known vulnerabilities | ADR-0001, `raw/phase1-backend-tests.txt` |
| Reproducible backend startup (T01) | **Pass.** Clean volume → healthy in 6.1 s; migrations applied by owner role; API connects as DML-only role; repeated boot idempotent | `raw/phase0-t01-clean-boot.txt`, `raw/phase1-compose-e2e.txt` |
| Reproducible APK build | **Pass in two independent environments**: this container and GitHub Actions (ubuntu-24.04, Temurin 21) | `android/`, `.github/workflows/ci.yml` |
| CI (independent re-run) | **Pass — run 45355378246 on commit 388cea8, 2026-11-24.** Job `backend`: ruff, 57 pytest on PostgreSQL 18.7 service, pip-audit clean. Job `integration-android`: compose stack up, two-account e2e across a DB+API restart, `LiveServerTest` PASSED (`LIVE OK`), `LiveUiFlowTest` PASSED, `ColdStartTest` PASSED, lint, pilot APK built and uploaded as artifact `pilot-apk` (CI build SHA-256 `46569fec…59bf1de`; differs from the locally built file because debug builds are not bit-reproducible — both are signed with the same pilot key) | GitHub Actions run 45355378246 |
| Requirements map | Done | `docs/REQUIREMENTS_TRACEABILITY.csv` |

**Phase 0 verdict: complete.**

CI follow-ups (non-blocking): `actions/upload-artifact@v5` runs on a deprecated Node 20 runtime
(GitHub forces Node 24; works); `createAndroidComposeRule` v1 and `PasswordVisualTransformation`
are deprecated APIs to migrate in Phase 2.

## Phase 1 — Live vertical slice
Implemented: migrations; registration/login/refresh rotation/logout/session list+revoke; communities
(create, browse, join/leave idempotent, owner/moderator roles, edit); text and link posts with
idempotency keys; threaded comments with DB-enforced same-post parents, bounded tree reads and
"continue thread"; transactional votes with karma; Home/All/community feeds with hot/new/top/
controversial and keyset cursors; author delete and audited moderator removal; minimal Android UI
for all of the above.

| Exit criterion | Result | Evidence |
|---|---|---|
| Two accounts on separate clients interact against a real server | **Pass on real server, JVM clients.** (a) stdlib Python HTTP script, two accounts; (b) the app's shipped Kotlin client, two independent client instances; (c) the **real app UI** (MainActivity + Compose screens, Robolectric on JVM) as account A while account B uses a second client — post, comment, reply, comment vote, post vote, karma all confirmed server-side | `raw/phase1-compose-e2e.txt`, `raw/phase1-android-tests.txt` (`LiveServerTest`, `LiveUiFlowTest`) |
| Restart preserves state (T14) | **Pass**: full `compose down`/`up`, API-only restart, DB+API restart; app-side cold start restores session from persisted server + tokens and drops a revoked session | `raw/phase1-compose-e2e.txt`, `raw/phase0-t01-clean-boot.txt`, `ColdStartTest` |
| Authorization tests pass (T15) | **Pass**: cross-account edit/delete/mod actions rejected with no side effects; moderation scoped per community; anonymous writes 401 | `raw/phase1-backend-tests.txt` |
| Physical Android devices | **Not done — cannot be done here** (no device, no KVM). Needs the owner: install the APK on two phones and run the checklist below | — |

**Phase 1 verdict: implemented and verified against a real server; NOT yet accepted**, because the
roadmap gate says "separate clients" and the release rules require real-device evidence. I have not
claimed device verification.

### Owner device checklist (closes the Phase 1 gate)
1. Start the server (OPERATIONS §1), note its LAN address.
2. Install `threadhall-0.1.0-pilot.apk` on two phones (or a phone and an emulator). Verify checksum
   `0c7777a9b485d151e29dce1cad4c085d30b073ba1d0d3cefaa8a7c95b3cbd762`.
3. Phone A: connect, create account, create community, write a post.
4. Phone B: connect, create a second account, join the community, comment on the post.
5. Phone A: open the post, reply to B, upvote B's comment. Phone B: upvote A's post.
6. Both: Profile → Refresh shows karma 1. Force-stop both apps and restart the server; reopen — both
   still signed in, thread intact. Record a screen video or `adb logcat` excerpt into `docs/evidence/`.

## Defects found and fixed during verification (root causes)
1. Community-creation rate limit counted rejected attempts → 5 typos locked a user out for an hour.
   Fixed: validate first, limit configurable (`COMMUNITY_CREATE_PER_HOUR`).
2. Control-character regex was rewritten with literal invisible characters by an auto-fix step →
   replaced by explicit escapes; repository scanned for bidi/zero-width characters.
3. UI coroutines resumed on the network thread in the test environment, so navigation ran off the
   main thread ("Something went wrong" after a successful sign-up). Fixed: all UI-launched work is
   confined to `Dispatchers.Main.immediate`; unexpected failures are now logged.
4. Community/feed lists stayed stale after the user's own post → added a content-changed signal so
   lists refresh after the user's writes.
5. Modal reply dialog could not be driven reliably → replaced with an inline, keyboard-aware composer.

## Known limitations (Phase 1 build)
- No offline cache or queued writes (Phase 4). Offline shows errors with Retry; sessions survive.
- No search, inbox, bookmarks, profiles beyond self/user posts, pinned posts, Markdown rendering,
  edit UI for posts/comments (API supports edit), moderator UI (API supports removal) — Phase 2/5.
- No password recovery (OD-09), account deletion/export, reports/appeals (Phase 5).
- Rate limiting is in-process (single server). No TLS termination, backups automation, monitoring.
- Release APK builds and minifies but is unsigned (no owner key) and **untested on a device**.
- Idempotency keys are kept indefinitely until the Phase 4 cleanup job exists.

## Next blockers / owner actions
1. Run the device checklist above (closes Phase 1).
2. Decide OD-01 (name) before anything public; OD-12 (license).
3. Phase 2 (classic experience: search, profiles, inbox, bookmarks, prefs, accessibility audit) can
   start now; it does not depend on Phase 3 historical imports.
