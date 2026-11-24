# Implementation Status

Status words: **verified** (live or real-data evidence exists), **implemented** (code plus passing offline
tests, without live proof of the capability), **contract** (types only), **specified** (design only),
**not started**.

## 1. Summary by area

| Area | Status | Evidence |
|---|---|---|
| Taxonomy v0.1.0 (18 entries × 12 facets = 216 facets: 119 sourced, 83 analysis, 14 unverified) | implemented; 160/161 citations **verified live** | `evidence/phase0/citation_report.json` |
| Source registry v0.1.0 (58 references, 36 candidate ingestion sources) | implemented; reachability probed live | `evidence/phase0/source_probe_report.json` |
| Data contracts v0.1.0 | implemented (unit-tested; no persistence yet) | `tests/unit/test_contracts.py` |
| Scope policy and hard limits | implemented (unit-tested) | `tests/unit/test_scope.py` |
| Bounded fetcher and text extraction (HTML, text, PDF) | implemented; exercised live (58 retrievals) and against a local HTTP server | citation report; `tests/unit/test_fetch_and_citations.py` |
| Citation verifier | **verified**: live run, plus a live negative control that rejects fabricated and off-by-one claims | `evidence/phase0/test_results.txt` |
| Benchmark pre-registration B01–B06 | implemented (definitions only; **no benchmark run**) | `data/benchmarks/definitions.yaml` |
| Generated docs with drift tests | implemented | `tests/unit/test_project_integrity.py` |
| Ingestion adapters, storage, evidence store, KG | not started (Phase 1) | — |
| Signatures and recognition | contract / specified (Phase 2) | — |
| Open-set, anomaly, hypotheses | contract / specified (Phase 3) | — |
| Hidden-value engine | specified (Phase 4) | — |
| Orchestrator, dashboard | contract / not started (Phase 5) | — |

## 2. Verification record (2026-11-24)

| Step | Command | Result |
|---|---|---|
| Baseline | repository inspection | Empty repository, no commits, 0 tests |
| Offline validation | `python -m abyss validate` | OK (exit 0) |
| Unit tier | `python -m pytest` | **99 passed, 2 skipped** (the 2 skips are the live tests, run separately below) |
| Live tier | `ABYSS_LIVE=1 python -m pytest tests/live` | **2 passed** (negative control; full taxonomy check with 0 QUOTE_NOT_FOUND) |
| Citation evidence | `python -m abyss verify-citations` at commit `321cc12` (clean tree) | 161 citations: 160 VERIFIED, 1 SOURCE_UNEXTRACTABLE; 58 sources (57 ok, 1 unextractable). Exit 4 = only source-availability problems |
| Reachability | `python -m abyss probe-sources` at `321cc12` | 36 probed: 30 ok, 3 rate-limited (Codeberg, Semantic Scholar, Wikipedia), 2 failed (SourceHut 502, Wayback CDX reset), 1 blocked (GitHub API 403) |

Full console output: `evidence/phase0/test_results.txt`. The JSON reports record the commit, the dirty flag
(false), the environment and the SHA-256 of every input file.

## 3. Environment and versions (tested, not pinned)

Python 3.13.18; pydantic 2.13.5; PyYAML 6.0.3; pytest 9.1.1; pypdf 6.17.0; poppler `pdftotext`; Linux x86_64
container with 4 CPU, 15 GiB RAM, no GPU, and HTTPS egress through a policy proxy. A lock file and a container
recipe are Phase 1 work (R23).

## 4. What isn't claimed

- No discovery has been made. No benchmark has been run. No classifier exists.
- VERIFIED citations prove the quote was present at retrieval time, not that the facet wording is faithful or the source correct.
- Reachability results apply to this cloud environment only.
