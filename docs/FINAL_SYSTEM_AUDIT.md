# Final System Audit

**Status: not started.** This is a Phase 7 deliverable. This file records the audit checklist now, so the
release criteria are known in advance and can't be redefined at the end.

## Release checklist (each item needs an evidence path)

| # | Criterion | Evidence required | Result |
|---|---|---|---|
| 1 | Every requirement R00–R24 is `verified` or has a documented, accepted limitation | REQUIREMENTS_TRACEABILITY.md | — |
| 2 | Full regression (T01–T24) on a pinned environment at a tagged commit | Test log with commit and lock-file hash | — |
| 3 | B01–B06 results reported with CIs, failures and dataset versions | BENCHMARK_RESULTS.md | — |
| 4 | Zero fabricated citations; 100% traceability of verified reports (B06) | Re-verification report | — |
| 5 | 72-hour bounded autonomous run without an unrecovered critical error | Timestamped logs, budgets, outputs | — |
| 6 | Kill/restore with no loss of committed evidence | T11 log | — |
| 7 | Security audit: T12 suite passes; dependency review; no critical findings open | SECURITY_AUDIT.md | — |
| 8 | Reproducible release (container plus lock file) built from a clean checkout | Build log | — |
| 9 | Independent review (owner or third party) of claims and documentation | Review record | — |
| 10 | Known limitations current | KNOWN_LIMITATIONS.md | — |
