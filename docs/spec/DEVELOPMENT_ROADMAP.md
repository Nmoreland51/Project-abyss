# Phased development roadmap
All phases: audit baseline, implement cohesive changes, run relevant real and synthetic tests, document actual outcomes, commit, and report remaining risks. Do not declare phase complete without artifacts and evidence. No time estimates without team and resource baseline.

| Phase | Scope | Exit gate |
|---|---|---|
| 0 Foundation | Audit repository if present, decide platform scope, distinct branding, code/data rights, threat model, ADRs, dependency versions, CI, dev compose | Reproducible backend startup and APK build; requirements map; source permission registry; decisions documented |
| 1 Live vertical slice | DB migrations, authentication, community create/join, post create/list, comment reply, vote transaction; minimal Android UI | Two accounts on separate clients interact against real server; restart preserves state; authorization tests pass |
| 2 Classic experience | compact feeds, threaded UI, sorts, profiles, bookmarks, search, inbox, preferences, accessibility | Real device navigates all core flows without archive UI; search/feeds stable; UI and API tests pass |
| 3 Historical foundation | staging importer, source provenance, permission decisions, dedupe, normal feed integration, local replies, coverage and removal | Small rights-cleared public or synthetic fixture import; replay yields no duplicates; source outage does not affect live reads/writes; historical identity separation verified |
| 4 Mobile resilience | Room cache, WorkManager sync, idempotent queue, offline state, pagination, crash recovery | Airplane-mode cache and reconnection tested; no duplicated posts/votes; sign-out clears private data |
| 5 Media and governance | uploads, storage quotas, safe rendering, reporting/blocking, scoped mod tools, appeals, deletion, policy settings | Synthetic media validation; report/remove/appeal end-to-end; no removed result in feed/search/cache; explicit governance review |
| 6 Deployment and scale | staging TLS, backups, observability, load tests, migration/rollback, independent uptime, optional read-only Abyss integration | Restore drill passes; measured performance and security review; no external archive dependency; integration optional |
| 7 Release | signed APK, install/update on actual Android, clean-server deploy, operational policy and legal/data review, final acceptance | all required tests pass, signed artifact + checksum, real-device evidence, release notes, known limitations and runbook; public launch separately approved |

## MVP boundary
Phase 1 + minimal Phase 2 is a real live social platform. Do not block core on archival ingestion. Phase 3 adds authorized historical foundation. Public release requires governance and reliability gates; media and optional Abyss integration can be later if explicitly excluded from MVP. Scope changes must be recorded with reasons, tradeoffs and tests.

## Risks and mitigation
- Cold start: small consenting community, useful seed posts, invitations; no fake users or engagement.
- Archive availability and rights: staged optional adapter, source permission manifest, fallback to original content.
- Scaling: start with one modular service, benchmark before splitting; limit quotas and storage growth.
- Old code vulnerabilities: modern stack, audited reference use, dependency scanning.
- Android fragmentation: emulator matrix and actual device testing.
- Operational overhead: private pilot before public deployment, backup/restore and escalation owner.
