# Testing strategy and acceptance matrix
Proposed gates, not completed tests. Record commit, environment, command, dataset, output, result and limitations. CI runs unit/integration; staging runs real DB, actual HTTP and device tests. Mock-only success never establishes live readiness.

| Test ID | Scenario | Expected result |
|---|---|---|
| T01 | clean compose boot and migrations | readiness healthy, repeatable |
| T02 | register two users, login/logout/refresh | independent sessions, revoke works |
| T03 | create/join community | memberships persistent, role checks enforced |
| T04 | post and comment from two devices | visible in normal feed/thread, real server |
| T05 | concurrent vote retries and reversal | one vote per user/target, correct score/karma |
| T06 | new/top/hot/controversial, pinned, cursor | deterministic fixtures, no duplicates in snapshot |
| T07 | deep threads, wrong parent, edit/delete | correct hierarchy, bounded UI, invalid parent rejected |
| T08 | search text/community and visibility | expected results, no removed records |
| T09 | import permitted fixtures twice | dedupe, stable IDs, provenance, no fake authors |
| T10 | missing parent/score/capture and malformed row | explicit missing metadata, quarantine and resume |
| T11 | archive source outage after import | live posting/search/votes unaffected |
| T12 | historical timestamp and local reply | original date preserved, new author local, score separate |
| T13 | offline cache and reconnect | read cache visible, pending status, retry no duplicates |
| T14 | restart app/server, migrations | data retained; schema upgrades tested |
| T15 | unauthorized cross-account writes/mod actions | server rejects, no leakage |
| T16 | injection, Markdown/XSS, SSRF, token misuse | inputs safe, no secrets leaked |
| T17 | synthetic media wrong MIME, quota, oversized | validation and lifecycle behave as documented |
| T18 | report/remove/appeal/block | correct scope, audit, visibility propagation |
| T19 | removal then attempted reimport | tombstone respected; search/cache/media cleared |
| T20 | account export/delete and session revocation | ownership verified, private data removed per policy |
| T21 | load baseline and failure injection | measured p95, graceful errors, backoff |
| T22 | backup restore and migration rollback | recovered data and documented RPO/RTO |
| T23 | accessibility, light/dark, text scaling | usable real-device flows |
| T24 | signed APK install/update | valid signature, app opens, no data loss |
| T25 | optional Abyss read-only integration | visibility respected, no private data, disabled works |
| T26 | normal launch experience | live Home feed; no mandatory date picker or archive browser |
| T27 | notification/bookmark/profile | durable user state; scoped access |
| T28 | source permission unresolved | no unauthorized publication, decision recorded |

## Performance protocol
Seed 100k synthetic posts with realistic community/comment distribution. Declare machine, network, database versions, dataset seed, cold/warm state; run 20 concurrent users mixed reads/writes for 10 minutes after warmup. Proposed p95 feed API <=500ms, search <=1s, vote <=500ms, cached render <=500ms on declared reference device. Report errors, p50/p95/p99, throughput, memory, CPU, DB plans; do not adjust targets after results without reason. Increase load until saturation and record bottleneck. No test traffic on third-party archives without authorization.

## Public release gates
All required scenarios pass, no unresolved critical security defect, backup restore evidenced, permission and governance review complete, signed APK checksum and real-device video/logs available, operational runbook and known limitations published. Optional features marked deferred, not passed. A green build alone is not release acceptance.
