# ADR-0005 Android client (Phase 1 scope)

Status: accepted · Date: 2026-11-24

- **UI:** Jetpack Compose + Material 3, single activity, Navigation Compose. Bottom tabs Home / All /
  Communities / Profile. Launch opens the normal Home feed (anonymous users get All content); there is
  no archive browser or date picker (T26).
- **Classic compact rows:** vote column (▲ score ▼), title, `c/community · u/author · age`, link
  domain, comment count. Threads are flattened into a lazy list with capped visual indentation
  (6 levels) and "continue thread" rows — no recursive unbounded composition.
- **Server is authoritative.** Votes, posts and comments update the UI only after the server confirms.
  While a vote is in flight the arrows are disabled and a spinner replaces the score. Post and comment
  drafts carry a client-generated idempotency key, so pressing Submit again after a timeout cannot
  create duplicates.
- **Offline cache (Room) and queued writes (WorkManager) are Phase 4 (R12)**, deliberately not built
  in Phase 1. Today, offline means: lists show an error with Retry; signed-in state is kept.
- **Server address is user-configured** on first run. The app contacts no other host (no analytics,
  no crash reporting SDK, no third-party APIs). Links open in the system browser only when tapped.
- **Builds:** `debug` = *pilot* build (`dev.threadhall.app.pilot`, debuggable, http:// allowed on a
  private network with a visible warning, signed with the shared pilot key — OD-03/OD-04).
  `release` = minified, HTTPS-only, signed only with an owner-supplied key from environment variables.
- **Accessibility:** content descriptions on vote/score controls, collapse state descriptions, 40dp+
  touch targets, all text in `sp` so system font scaling applies, light and dark colour schemes.
  A formal T23 audit on a real device is a Phase 2 gate.
- **compileSdk 37.2** is required by Compose 1.13/Navigation 2.10; targetSdk stays 36 so runtime
  behaviour changes of API 37 are not opted into without testing.
