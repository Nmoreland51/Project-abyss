# Benchmark Results

**No benchmark has been run.** No dataset exists yet. The definitions below were pre-registered on
2026-11-24 in `data/benchmarks/definitions.yaml` (v0.1.0) before any data collection, so that metrics can't
be tuned to results.

| ID | Benchmark | Phase | Proposed target(s) | Status |
|---|---|---|---|---|
| B01 | Known-architecture-family recognition | 2 | macro F1 ≥ 0.90 (MASTER_AUDIT s9) | defined_not_run |
| B02 | Withheld-family (open-set) recognition | 3 | unknown recall ≥ 0.80; false unknown ≤ 0.05 (MASTER_AUDIT s9) | defined_not_run |
| B03 | Calibration and abstention | 3 | none yet | defined_not_run |
| B04 | Anomaly false positives under ordinary change | 3 | false-anomaly rate ≤ 0.10 (agent proposal, D-007) | defined_not_run |
| B05 | Hidden-value usefulness compared with a conventional baseline | 4 | verified-claim rate = 1.0 (MASTER_AUDIT); novelty@5 ≥ 0.5 (agent proposal) | defined_not_run |
| B06 | Evidence traceability and fabrication in system reports | 1 | traceability = 1.0; fabricated citations = 0 (MASTER_AUDIT s9) | defined_not_run |

## Phase 0 test results (these are test results, not benchmarks)

The taxonomy citation check is a **test** (T21/T08) of the Phase 0 deliverable. It isn't B06, which measures
reports that Abyss itself generates.

| Measure | Value | Evidence |
|---|---|---|
| Citations checked live | 161 | `evidence/phase0/citation_report.json` |
| VERIFIED | 160 (99.4%) | same |
| QUOTE_NOT_FOUND | 0 | same |
| SOURCE_UNEXTRACTABLE | 1 (Kademlia PDF, font-encoded text layer) | same |
| Sources retrieved | 58 (57 ok, 1 text-unextractable) | same |
| Negative control (fabricated and off-by-one claims rejected) | see `evidence/phase0/test_results.txt` (live tier) | `tests/live/test_live_citations.py` |
| Candidate ingestion sources reachable here | 30 of 36 ok; 3 rate-limited; 2 failed; 1 blocked (varies between runs; see SCOPE_AND_RESTRICTIONS s3) | `evidence/phase0/source_probe_report.json` |

Limitation: VERIFIED shows that the quote was present in the retrieved text. Whether each facet's paraphrase is
faithful to its quotes hasn't been independently reviewed (GAP P0-3).
