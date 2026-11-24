# Implementation Status

Status words: **verified** (live or real-data evidence exists), **implemented** (code plus passing offline
tests, without live proof of the capability), **contract** (types only), **specified** (design only),
**not started**.

| Area | Status | Evidence |
|---|---|---|
| Taxonomy v0.1.0 (18 entries, 12 facets each) | implemented; citations verified live (see below) | `evidence/phase0/citation_report.json` |
| Source registry v0.1.0 | implemented; reachability probed live | `evidence/phase0/source_probe_report.json` |
| Data contracts v0.1.0 | implemented (unit-tested) | `tests/unit/test_contracts.py` |
| Scope policy | implemented (unit-tested) | `tests/unit/test_scope.py` |
| Fetcher and text extraction | implemented; exercised live by the citation run | citation report |
| Citation verifier | verified (live run plus negative control) | citation report; `evidence/phase0/test_results.txt` |
| Benchmark pre-registration | implemented (definitions only; no runs) | `data/benchmarks/definitions.yaml` |
| Ingestion adapters, storage, KG | not started (Phase 1) | — |
| Recognition, signatures | specified / contract (Phase 2) | — |
| Open-set, anomaly, hypotheses | specified / contract (Phase 3) | — |
| Hidden-value engine | specified (Phase 4) | — |
| Orchestrator, dashboard | contract / not started (Phase 5) | — |

Final Phase 0 run numbers are recorded in the "Verification record" section once the run completes.
